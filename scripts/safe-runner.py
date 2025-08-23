#!/usr/bin/env python3
"""
Safe Script Runner for Orchestra
Validates and safely executes scripts with security checks.
"""

import argparse
import hashlib
import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ANSI colors for output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_error(msg: str) -> None:
    print(f"{Colors.RED}❌ ERROR: {msg}{Colors.END}", file=sys.stderr)


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  WARNING: {msg}{Colors.END}")


def print_info(msg: str) -> None:
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")


def print_header(msg: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")


class ScriptValidator:
    """Validates scripts before execution."""

    ALLOWED_INTERPRETERS = {
        "python",
        "python3",
        "python3.13",
        "bash",
        "sh",
        "zsh",
        "env",
    }

    DANGEROUS_PATTERNS = [
        # Actual dangerous commands (not just mentions in strings or comments)
        (r"^\s*rm\s+-rf\s+/[^#]*$", "Dangerous recursive delete of root"),
        (r"^\s*chmod\s+777", "Dangerous permission change"),
        (r"curl.*\|\s*bash", "Piping curl to bash"),
        (r"wget.*\|\s*bash", "Piping wget to bash"),
        (r"^\s*eval\s+\$[^#\"']*$", "Dynamic eval usage"),
        (r"^\s*exec\s+\$[^#\"']*$", "Dynamic exec usage"),
        # Network operations that could be dangerous (actual usage, not examples)
        (r"^\s*nc\s+-[^l]*e", "Netcat with execute flag"),
        (r"^\s*dd\s+.*of=/dev/", "Direct disk write"),
        # Only flag actual sudo NOPASSWD configurations, not examples
        (r"^\s*.*\s+ALL=\(ALL\)\s+NOPASSWD:", "Passwordless sudo configuration"),
    ]

    SAFE_SCRIPT_HASHES = {
        # Add known good script hashes here
        # "sha256_hash": "script_description"
    }

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    def validate_script_path(self, script_path: Path) -> bool:
        """Validate that the script path is safe."""
        try:
            # Convert to absolute path and resolve
            abs_path = script_path.resolve()

            # Must be within project directory
            if not str(abs_path).startswith(str(self.project_root.resolve())):
                print_error(f"Script must be within project directory: {abs_path}")
                return False

            # Must exist and be a file
            if not abs_path.exists():
                print_error(f"Script does not exist: {abs_path}")
                return False

            if not abs_path.is_file():
                print_error(f"Path is not a file: {abs_path}")
                return False

            return True

        except Exception as e:
            print_error(f"Error validating script path: {e}")
            return False

    def check_file_permissions(self, script_path: Path) -> bool:
        """Check file permissions are safe."""
        try:
            file_stat = script_path.stat()
            mode = stat.filemode(file_stat.st_mode)

            # Check if world-writable
            if file_stat.st_mode & stat.S_IWOTH:
                print_error(f"Script is world-writable: {mode}")
                return False

            # Check if group-writable (warning only)
            if file_stat.st_mode & stat.S_IWGRP:
                print_warning(f"Script is group-writable: {mode}")

            print_info(f"File permissions: {mode}")
            return True

        except Exception as e:
            print_error(f"Error checking permissions: {e}")
            return False

    def validate_shebang(self, script_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate the script's shebang line."""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()

            if not first_line.startswith("#!"):
                print_warning("No shebang found")
                return True, None

            # Extract interpreter
            shebang = first_line[2:].strip()
            interpreter_parts = shlex.split(shebang)

            if not interpreter_parts:
                print_error("Invalid shebang")
                return False, None

            interpreter = Path(interpreter_parts[0]).name

            # Check if interpreter is allowed
            if interpreter not in self.ALLOWED_INTERPRETERS:
                print_error(f"Interpreter not allowed: {interpreter}")
                print_info(
                    f"Allowed interpreters: {', '.join(self.ALLOWED_INTERPRETERS)}"
                )
                return False, None

            print_info(f"Interpreter: {interpreter}")
            return True, interpreter

        except Exception as e:
            print_error(f"Error reading script: {e}")
            return False, None

    def scan_for_dangerous_patterns(self, script_path: Path) -> bool:
        """Scan script content for dangerous patterns."""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()

            found_issues = []

            for pattern, description in self.DANGEROUS_PATTERNS:
                import re

                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    found_issues.append((pattern, description))

            if found_issues:
                print_error("Dangerous patterns found:")
                for pattern, description in found_issues:
                    print(f"  - {description}")
                return False

            print_success("No dangerous patterns found")
            return True

        except Exception as e:
            print_error(f"Error scanning script content: {e}")
            return False

    def calculate_script_hash(self, script_path: Path) -> str:
        """Calculate SHA256 hash of script."""
        try:
            with open(script_path, "rb") as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except Exception as e:
            print_error(f"Error calculating hash: {e}")
            return ""

    def validate_script(self, script_path: Path) -> Tuple[bool, Optional[str]]:
        """Perform comprehensive script validation."""
        print_header("Script Validation")

        # Basic path validation
        if not self.validate_script_path(script_path):
            return False, None

        # Permission checks
        if not self.check_file_permissions(script_path):
            return False, None

        # Shebang validation
        valid_shebang, interpreter = self.validate_shebang(script_path)
        if not valid_shebang:
            return False, None

        # Content scanning
        if not self.scan_for_dangerous_patterns(script_path):
            return False, None

        # Hash verification (informational)
        script_hash = self.calculate_script_hash(script_path)
        if script_hash:
            print_info(f"Script hash: {script_hash}")
            if script_hash in self.SAFE_SCRIPT_HASHES:
                print_success(
                    f"Known safe script: {self.SAFE_SCRIPT_HASHES[script_hash]}"
                )

        print_success("Script validation passed")
        return True, interpreter


class SafeScriptRunner:
    """Safely executes validated scripts."""

    def __init__(self):
        self.validator = ScriptValidator()

    def create_safe_environment(self) -> Dict[str, str]:
        """Create a safe execution environment."""
        # Start with minimal environment
        safe_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": os.environ.get("HOME", "/tmp"),
            "USER": os.environ.get("USER", "unknown"),
            "SHELL": "/bin/bash",
            "TERM": os.environ.get("TERM", "xterm"),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        }

        # Add project-specific variables if they exist
        project_vars = ["POETRY_HOME", "POETRY_VENV_PATH", "VIRTUAL_ENV"]
        for var in project_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]

        # Add current working directory
        safe_env["PWD"] = str(Path.cwd())

        return safe_env

    def run_script(
        self, script_path: Path, args: List[str], dry_run: bool = False
    ) -> int:
        """Run the script safely."""
        print_header("Script Execution")

        # Validate script first
        is_valid, interpreter = self.validator.validate_script(script_path)
        if not is_valid:
            print_error("Script validation failed")
            return 1

        # Prepare command
        if interpreter:
            cmd = [interpreter, str(script_path)] + args
        else:
            cmd = [str(script_path)] + args

        print_info(f"Command: {' '.join(shlex.quote(str(c)) for c in cmd)}")

        if dry_run:
            print_info("Dry run mode - script not executed")
            return 0

        # Create safe environment
        env = self.create_safe_environment()

        try:
            # Execute script
            print_info("Executing script...")
            result = subprocess.run(
                cmd, env=env, cwd=self.validator.project_root, text=True
            )

            if result.returncode == 0:
                print_success("Script completed successfully")
            else:
                print_error(f"Script failed with exit code: {result.returncode}")

            return result.returncode

        except KeyboardInterrupt:
            print_warning("Script execution interrupted by user")
            return 130
        except Exception as e:
            print_error(f"Error executing script: {e}")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Safely validate and execute Orchestra scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scripts/security_check.py
  %(prog)s scripts/daily-backup.sh --dry-run
  %(prog)s --validate-only scripts/setup.py
        """,
    )

    parser.add_argument("script", help="Path to script to execute")
    parser.add_argument("script_args", nargs="*", help="Arguments to pass to script")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate only, don't execute"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate, don't execute"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Convert script path
    script_path = Path(args.script)

    # Initialize runner
    runner = SafeScriptRunner()

    if args.validate_only:
        # Only validate
        is_valid, _ = runner.validator.validate_script(script_path)
        return 0 if is_valid else 1
    else:
        # Validate and run
        return runner.run_script(script_path, args.script_args, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
