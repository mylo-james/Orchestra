#!/usr/bin/env python3
"""
Validate All Scripts - Comprehensive safety check for all Orchestra scripts
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Add scripts directory to path to import safe-runner
sys.path.insert(0, str(Path(__file__).parent))

# Import safe-runner module (with hyphen in filename)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "safe_runner", Path(__file__).parent / "safe-runner.py"
)
safe_runner_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safe_runner_module)

ScriptValidator = safe_runner_module.ScriptValidator
Colors = safe_runner_module.Colors


def print_header(msg: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def find_all_scripts() -> List[Path]:
    """Find all executable scripts in the project."""
    project_root = Path(__file__).parent.parent

    script_patterns = [
        "scripts/*.py",
        "scripts/*.sh",
        "*.py",  # Root level Python scripts
    ]

    scripts = []
    for pattern in script_patterns:
        scripts.extend(project_root.glob(pattern))

    # Filter out this validation script and __pycache__ files
    scripts = [
        s
        for s in scripts
        if s.name != "validate-all-scripts.py"
        and "__pycache__" not in str(s)
        and s.is_file()
    ]

    return sorted(scripts)


def validate_script_with_details(
    validator: ScriptValidator, script_path: Path
) -> Tuple[bool, List[str]]:
    """Validate a script and return detailed results."""
    issues = []

    try:
        # Basic validation
        if not validator.validate_script_path(script_path):
            issues.append("Path validation failed")
            return False, issues

        # Permission check
        if not validator.check_file_permissions(script_path):
            issues.append("Permission check failed")

        # Shebang validation
        valid_shebang, interpreter = validator.validate_shebang(script_path)
        if not valid_shebang:
            issues.append("Invalid or missing shebang")

        # Content scanning
        if not validator.scan_for_dangerous_patterns(script_path):
            issues.append("Dangerous patterns detected")

        # Overall result
        is_valid = len(issues) == 0

        if is_valid:
            issues.append(f"Valid ({interpreter or 'no shebang'})")

        return is_valid, issues

    except Exception as e:
        issues.append(f"Validation error: {e}")
        return False, issues


def main():
    """Main validation function."""
    print_header("Orchestra Script Safety Validation")

    print(f"{Colors.CYAN}Finding all scripts in the project...{Colors.END}")

    scripts = find_all_scripts()

    if not scripts:
        print_warning("No scripts found to validate")
        return 0

    print(f"Found {len(scripts)} scripts to validate")

    validator = ScriptValidator()

    valid_scripts = []
    invalid_scripts = []

    print_header("Validation Results")

    for script in scripts:
        print(
            f"\n{Colors.CYAN}Validating: {script.relative_to(Path.cwd())}{Colors.END}"
        )

        is_valid, issues = validate_script_with_details(validator, script)

        if is_valid:
            valid_scripts.append(script)
            print_success(f"VALID: {issues[0]}")
        else:
            invalid_scripts.append((script, issues))
            print_error("INVALID:")
            for issue in issues:
                print(f"  - {issue}")

    # Summary
    print_header("Summary")

    total_scripts = len(scripts)
    valid_count = len(valid_scripts)
    invalid_count = len(invalid_scripts)

    print(f"Total scripts: {total_scripts}")
    print_success(f"Valid scripts: {valid_count}")

    if invalid_count > 0:
        print_error(f"Invalid scripts: {invalid_count}")
        print("\nScripts requiring attention:")
        for script, issues in invalid_scripts:
            print(f"  {script.relative_to(Path.cwd())}")
            for issue in issues:
                print(f"    - {issue}")
    else:
        print_success("All scripts are valid! 🎉")

    print("\nRecommendations:")
    print("1. Use 'python scripts/safe-runner.py <script>' to run scripts safely")
    print("2. Fix any issues identified above")
    print("3. Run 'python scripts/setup-security.py' to enhance security")
    print("4. Enable pre-commit hooks with 'poetry run pre-commit install'")

    return 0 if invalid_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
