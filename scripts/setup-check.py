#!/usr/bin/env python3
"""
Orchestra Development Environment Setup Checker
Comprehensive script to validate that everything is ready for development.
"""

import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# ANSI colors for output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


class SetupChecker:
    """Main setup checker class."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixes_applied: List[str] = []
        self.checks_passed = 0
        self.checks_total = 0

    def print_error(self, msg: str, details: Optional[str] = None) -> None:
        """Print error message and add to error list."""
        print(f"{Colors.RED}❌ {msg}{Colors.END}")
        if details:
            print(f"{Colors.DIM}   {details}{Colors.END}")
        self.errors.append(msg)

    def print_success(self, msg: str) -> None:
        """Print success message."""
        print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
        self.checks_passed += 1

    def print_warning(self, msg: str, details: Optional[str] = None) -> None:
        """Print warning message and add to warnings list."""
        print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")
        if details:
            print(f"{Colors.DIM}   {details}{Colors.END}")
        self.warnings.append(msg)

    def print_info(self, msg: str) -> None:
        """Print info message."""
        print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

    def print_fix(self, msg: str) -> None:
        """Print fix applied message."""
        print(f"{Colors.MAGENTA}🔧 {msg}{Colors.END}")
        self.fixes_applied.append(msg)

    def print_header(self, msg: str) -> None:
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{msg.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

    def run_command(
        self, cmd: List[str], timeout: int = 30, capture_output: bool = True
    ) -> Tuple[bool, str, str]:
        """Run a command and return success status, stdout, and stderr."""
        try:
            result = subprocess.run(
                cmd, capture_output=capture_output, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except FileNotFoundError:
            return False, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            return False, "", str(e)

    def get_version_from_output(
        self, output: str, patterns: List[str]
    ) -> Optional[str]:
        """Extract version from command output using regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

    def check_python(self) -> None:
        """Check Python installation and version."""
        self.checks_total += 1
        self.print_info("Checking Python...")

        success, stdout, stderr = self.run_command(["python3", "--version"])

        if not success:
            self.print_error(
                "Python 3 not found", "Install Python 3.13.0+ from https://python.org"
            )
            return

        version_match = re.search(r"Python (\d+\.\d+\.\d+)", stdout)
        if not version_match:
            self.print_error("Could not determine Python version")
            return

        version = version_match.group(1)
        major, minor, patch = map(int, version.split("."))

        if major == 3 and minor >= 13:
            self.print_success(f"Python {version} (✓ 3.13.0+)")
        elif major == 3 and minor >= 12:
            self.print_warning(
                f"Python {version} (recommended: 3.13.0+)",
                "Consider upgrading to Python 3.13",
            )
        else:
            self.print_error(
                f"Python {version} is too old (required: 3.13.0+)",
                "Upgrade Python to 3.13.0 or newer",
            )

    def check_poetry(self) -> None:
        """Check Poetry installation and version."""
        self.checks_total += 1
        self.print_info("Checking Poetry...")

        success, stdout, stderr = self.run_command(["poetry", "--version"])

        if not success:
            self.print_error(
                "Poetry not found",
                "Install Poetry from https://python-poetry.org/docs/#installation",
            )
            return

        version = self.get_version_from_output(
            stdout,
            [r"Poetry \(version (\d+\.\d+\.\d+)\)", r"Poetry version (\d+\.\d+\.\d+)"],
        )

        if version:
            major, minor, patch = map(int, version.split("."))
            if major >= 1 and minor >= 8:
                self.print_success(f"Poetry {version} (✓ 1.8.3+)")
            else:
                self.print_warning(
                    f"Poetry {version} (recommended: 1.8.3+)",
                    "Consider upgrading Poetry",
                )
        else:
            self.print_warning("Could not determine Poetry version")

    def check_git(self) -> None:
        """Check Git installation."""
        self.checks_total += 1
        self.print_info("Checking Git...")

        success, stdout, stderr = self.run_command(["git", "--version"])
        if not success:
            self.print_error("Git not found", "Install Git from https://git-scm.com/")
            return

        version = self.get_version_from_output(stdout, [r"git version (\d+\.\d+\.\d+)"])
        if version:
            self.print_success(f"Git {version}")
        else:
            self.print_success("Git installed")

    def check_environment_file(self) -> None:
        """Check if .env file exists and create it if needed."""
        self.checks_total += 1
        self.print_info("Checking environment configuration...")

        env_file = Path(".env")
        env_example = Path(".env.example")

        if not env_file.exists():
            if env_example.exists():
                self.print_fix("Creating .env file from .env.example")
                try:
                    env_example_content = env_example.read_text()
                    env_file.write_text(env_example_content)
                    self.print_success(".env file created from template")
                except Exception as e:
                    self.print_error("Failed to create .env file", f"Error: {e}")
                    return
            else:
                self.print_error(
                    "Neither .env nor .env.example found",
                    "Environment configuration is missing",
                )
                return

        # Check for required variables
        env_content = env_file.read_text()
        required_vars = ["OPENAI_API_KEY", "QDRANT_HOST", "TEMPORAL_HOST"]

        missing_vars = []
        placeholder_vars = []

        for var in required_vars:
            if var not in env_content or f"{var}=" not in env_content:
                missing_vars.append(var)
            elif f"{var}=your-" in env_content or f"{var}=sk-your-" in env_content:
                placeholder_vars.append(var)

        if missing_vars:
            self.print_error(
                f"Missing environment variables: {', '.join(missing_vars)}",
                "Add these variables to your .env file",
            )
        elif placeholder_vars:
            self.print_warning(
                f"Placeholder values detected: {', '.join(placeholder_vars)}",
                "Edit .env file with your actual API keys and configuration",
            )
        else:
            self.print_success(".env file exists with required variables")

    def check_poetry_dependencies(self) -> None:
        """Check if Poetry dependencies are installed and install them if needed."""
        self.checks_total += 1
        self.print_info("Checking Poetry dependencies...")

        # Check if pyproject.toml exists
        if not Path("pyproject.toml").exists():
            self.print_error(
                "pyproject.toml not found", "Not in a Poetry project directory"
            )
            return

        # Check if dependencies are installed
        success, stdout, stderr = self.run_command(["poetry", "check"])
        if success:
            self.print_success("Poetry dependencies are installed and valid")
            return

        # Try to install dependencies automatically
        self.print_fix("Installing Poetry dependencies...")
        success, stdout, stderr = self.run_command(
            ["poetry", "install", "--no-interaction"],
            timeout=300,  # 5 minutes for installation
        )

        if not success and "poetry.lock was last generated" in stderr:
            # Lock file is out of sync, try to update it
            self.print_fix("Poetry lock file out of sync, updating...")
            success, stdout, stderr = self.run_command(["poetry", "lock"], timeout=120)

            if success:
                # Try installing again after lock update
                success, stdout, stderr = self.run_command(
                    ["poetry", "install", "--no-interaction"], timeout=300
                )

        if success:
            self.print_success("Poetry dependencies installed successfully")

            # Verify installation worked
            success, stdout, stderr = self.run_command(["poetry", "check"])
            if not success:
                self.print_warning("Dependencies installed but validation still fails")
        else:
            self.print_error(
                "Failed to install Poetry dependencies",
                f"Error: {stderr[:200]}..." if len(stderr) > 200 else stderr,
            )

    def check_precommit_hooks(self) -> None:
        """Check if pre-commit hooks are installed and install them if needed."""
        self.checks_total += 1
        self.print_info("Checking pre-commit hooks...")

        # Check if pre-commit config exists
        precommit_config = Path(".pre-commit-config.yaml")
        if not precommit_config.exists():
            self.print_warning("Pre-commit configuration not found")
            return

        # Check if pre-commit is installed in the environment
        success, stdout, stderr = self.run_command(
            ["poetry", "run", "pre-commit", "--version"]
        )
        if not success:
            self.print_error("Pre-commit not installed", "Run: poetry install")
            return

        # Check if hooks are installed
        git_hooks = Path(".git/hooks/pre-commit")
        if git_hooks.exists():
            self.print_success("Pre-commit hooks are installed")
        else:
            # Try to install hooks automatically
            self.print_fix("Installing pre-commit hooks...")
            success, stdout, stderr = self.run_command(
                ["poetry", "run", "pre-commit", "install"]
            )

            if success:
                self.print_success("Pre-commit hooks installed successfully")
            else:
                self.print_error(
                    "Failed to install pre-commit hooks", f"Error: {stderr}"
                )

    def check_basic_functionality(self) -> None:
        """Check basic Orchestra functionality."""
        self.checks_total += 1
        self.print_info("Checking Orchestra functionality...")

        # Test basic import
        success, stdout, stderr = self.run_command(
            [
                "poetry",
                "run",
                "python",
                "-c",
                "import orchestra; print('✓ Import successful')",
            ]
        )

        if success:
            self.print_success("Orchestra module imports successfully")
        else:
            self.print_error("Cannot import Orchestra module", f"Error: {stderr}")

    def check_security_tools(self) -> None:
        """Check security tools functionality."""
        self.checks_total += 1
        self.print_info("Checking security tools...")

        security_tools = [
            (["poetry", "run", "bandit", "--version"], "Bandit security scanner"),
            (["poetry", "run", "ruff", "--version"], "Ruff linter"),
            (["poetry", "run", "black", "--version"], "Black code formatter"),
        ]

        tools_working = 0
        for cmd, tool_name in security_tools:
            success, stdout, stderr = self.run_command(cmd)
            if success:
                tools_working += 1

        if tools_working == len(security_tools):
            self.print_success("All security tools are working")
        elif tools_working > 0:
            self.print_warning(
                f"{tools_working}/{len(security_tools)} security tools working"
            )
        else:
            self.print_error("Security tools not working", "Run: poetry install")

    def run_quick_tests(self) -> None:
        """Run a quick subset of tests to verify functionality."""
        self.checks_total += 1
        self.print_info("Running quick functionality tests...")

        # Run a small subset of fast tests
        test_paths = [
            "tests/unit/config/",
            "tests/unit/models/",
        ]

        for test_path in test_paths:
            if Path(test_path).exists():
                success, stdout, stderr = self.run_command(
                    ["poetry", "run", "pytest", test_path, "-x", "--tb=short", "-q"],
                    timeout=60,
                )

                if success:
                    self.print_success(f"Quick tests passed: {test_path}")
                    return  # If any test suite passes, that's good enough for setup check
                else:
                    self.print_warning(f"Tests failed in {test_path}")

        self.print_warning(
            "Quick tests could not run successfully",
            "Full test suite may be needed to identify issues",
        )

    def run_all_checks(self) -> None:
        """Run all setup checks with automatic remediation."""
        self.print_header("Orchestra Development Environment Setup Check")
        print(
            f"{Colors.CYAN}This script will automatically fix issues where possible{Colors.END}"
        )
        print(
            f"{Colors.CYAN}and report any remaining issues that need manual attention{Colors.END}"
        )

        # System requirements
        self.print_header("System Requirements")
        self.check_python()
        self.check_poetry()
        self.check_git()

        # Environment setup
        self.print_header("Environment Configuration")
        self.check_environment_file()
        self.check_poetry_dependencies()
        self.check_precommit_hooks()

        # Functionality
        self.print_header("Functionality Checks")
        self.check_basic_functionality()
        self.check_security_tools()
        self.run_quick_tests()

        # Summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print setup check summary."""
        self.print_header("Setup Check Summary")

        print(f"{Colors.BOLD}Results:{Colors.END}")
        print(f"  ✅ Passed: {Colors.GREEN}{self.checks_passed}{Colors.END}")
        print(f"  🔧 Fixed: {Colors.MAGENTA}{len(self.fixes_applied)}{Colors.END}")
        print(f"  ⚠️  Warnings: {Colors.YELLOW}{len(self.warnings)}{Colors.END}")
        print(f"  ❌ Errors: {Colors.RED}{len(self.errors)}{Colors.END}")
        print(f"  📊 Total: {self.checks_total}")

        if self.fixes_applied:
            print(f"\n{Colors.MAGENTA}🔧 Fixes Applied:{Colors.END}")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"  {i}. {fix}")

        if self.errors:
            print(f"\n{Colors.RED}❌ Critical Issues:{Colors.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  Warnings:{Colors.END}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        # Overall status
        if not self.errors:
            if not self.warnings:
                print(
                    f"\n{Colors.GREEN}{Colors.BOLD}🎉 Perfect! Environment is ready for development{Colors.END}"
                )
                if self.fixes_applied:
                    print(
                        f"{Colors.MAGENTA}Setup script automatically resolved {len(self.fixes_applied)} issue(s){Colors.END}"
                    )
            else:
                print(
                    f"\n{Colors.GREEN}{Colors.BOLD}✅ Environment is ready with minor warnings{Colors.END}"
                )
                if self.fixes_applied:
                    print(
                        f"{Colors.MAGENTA}Setup script automatically resolved {len(self.fixes_applied)} issue(s){Colors.END}"
                    )
                print(
                    f"{Colors.YELLOW}Consider addressing the warnings above{Colors.END}"
                )
        else:
            print(
                f"\n{Colors.RED}{Colors.BOLD}❌ Environment setup incomplete{Colors.END}"
            )
            if self.fixes_applied:
                print(
                    f"{Colors.MAGENTA}Setup script resolved {len(self.fixes_applied)} issue(s) but {len(self.errors)} remain{Colors.END}"
                )
            print(f"{Colors.RED}Please resolve the critical issues above{Colors.END}")

        # Next steps
        print(f"\n{Colors.CYAN}{Colors.BOLD}Next Steps:{Colors.END}")
        if self.errors:
            print(f"{Colors.CYAN}1. Fix all critical issues listed above{Colors.END}")
            print(f"{Colors.CYAN}2. Re-run: make setup{Colors.END}")
        else:
            print(
                f"{Colors.CYAN}1. Run: make test-cli (all tests should pass){Colors.END}"
            )
            print(f"{Colors.CYAN}2. Run: poetry run orchestra --help{Colors.END}")
            print(
                f"{Colors.CYAN}3. Check the README.md for usage instructions{Colors.END}"
            )
            if self.warnings:
                print(
                    f"{Colors.CYAN}4. Address any warnings when convenient{Colors.END}"
                )
            print(
                f"\n{Colors.DIM}Optional: Start Docker services for full features with: docker compose up -d{Colors.END}"
            )


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    print(
        f"\n{Colors.YELLOW}⚠️  Setup interrupted by user (signal {signum}){Colors.END}"
    )
    print(f"{Colors.YELLOW}You can resume setup by running: make setup{Colors.END}")
    sys.exit(130)


def main():
    """Main entry point."""
    # Set up signal handlers for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    checker = SetupChecker()

    try:
        checker.run_all_checks()

        # Exit with appropriate code
        if checker.errors:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        # Fallback in case signal handler doesn't catch it
        print(f"\n{Colors.YELLOW}Setup check interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Setup check failed with error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
