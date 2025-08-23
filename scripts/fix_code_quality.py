#!/usr/bin/env python3
"""Script to automatically fix code quality issues."""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str) -> None:
    """Print a colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(50)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def run_command(command: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print_info(f"Running: {description}")
    print(f"{Colors.CYAN}Command: {' '.join(command)}{Colors.END}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, cwd=Path.cwd())

        if result.returncode == 0:
            print_success(f"{description} completed")
            return True, result.stdout
        else:
            print_error(f"{description} failed")
            if result.stderr.strip():
                print(f"{Colors.RED}{result.stderr.strip()}{Colors.END}")
            return False, result.stderr

    except FileNotFoundError:
        print_error(f"Command not found: {command[0]}")
        return False, f"Command not found: {command[0]}"
    except Exception as e:
        print_error(f"Error running {description}: {e}")
        return False, str(e)


def fix_formatting() -> bool:
    """Fix code formatting issues."""
    print_header("Fixing Code Formatting")

    success = True

    # Run Black to fix formatting
    black_success, _ = run_command(
        ["poetry", "run", "black", "src/", "tests/"], "Black code formatting"
    )
    success = success and black_success

    # Run isort to fix import sorting
    isort_success, _ = run_command(
        ["poetry", "run", "isort", "src/", "tests/"], "isort import sorting"
    )
    success = success and isort_success

    return success


def fix_linting() -> bool:
    """Fix linting issues that can be auto-fixed."""
    print_header("Fixing Linting Issues")

    # Run Ruff with --fix to auto-fix issues
    success, _ = run_command(
        ["poetry", "run", "ruff", "check", "--fix", "src/", "tests/"], "Ruff auto-fix"
    )

    return success


def update_pre_commit() -> bool:
    """Update and run pre-commit hooks."""
    print_header("Updating Pre-commit Hooks")

    success = True

    # Update pre-commit hooks
    update_success, _ = run_command(
        ["poetry", "run", "pre-commit", "autoupdate"], "Update pre-commit hooks"
    )
    success = success and update_success

    # Run pre-commit on all files
    run_success, _ = run_command(
        ["poetry", "run", "pre-commit", "run", "--all-files"],
        "Run pre-commit on all files",
    )
    # Don't fail if pre-commit finds issues, we'll fix them iteratively

    return success


def check_remaining_issues() -> Tuple[bool, List[str]]:
    """Check for remaining issues that need manual fixing."""
    print_header("Checking Remaining Issues")

    issues = []

    # Check Black formatting
    black_success, black_output = run_command(
        ["poetry", "run", "black", "--check", "src/", "tests/"],
        "Check Black formatting",
    )
    if not black_success:
        issues.append("Black formatting issues remain")

    # Check isort
    isort_success, isort_output = run_command(
        ["poetry", "run", "isort", "--check-only", "src/", "tests/"], "Check isort"
    )
    if not isort_success:
        issues.append("Import sorting issues remain")

    # Check Ruff
    ruff_success, ruff_output = run_command(
        ["poetry", "run", "ruff", "check", "src/", "tests/"], "Check Ruff linting"
    )
    if not ruff_success:
        issues.append("Ruff linting issues remain")

    # Check MyPy (informational only)
    mypy_success, mypy_output = run_command(
        ["poetry", "run", "mypy", "src/"], "Check MyPy type hints"
    )
    if not mypy_success:
        issues.append("MyPy type checking issues (may require manual fixes)")

    return len(issues) == 0, issues


def main():
    """Main function to fix code quality issues."""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("🔧 Orchestra Code Quality Fixer")
    print("Automatically fixing code quality issues")
    print(f"{Colors.END}")

    # Fix formatting
    if not fix_formatting():
        print_error("Failed to fix formatting issues")
        sys.exit(1)

    # Fix linting
    if not fix_linting():
        print_error("Failed to fix linting issues")
        sys.exit(1)

    # Update pre-commit
    if not update_pre_commit():
        print_error("Failed to update pre-commit hooks")
        # Don't exit, continue to check issues

    # Check remaining issues
    all_fixed, remaining_issues = check_remaining_issues()

    print_header("Summary")

    if all_fixed:
        print_success("All auto-fixable issues have been resolved! ✨")
        print_info("Run 'git diff' to see what was changed")
        print_info("Don't forget to commit your changes")
    else:
        print_error("Some issues require manual fixing:")
        for issue in remaining_issues:
            print(f"  - {issue}")
        print_info("Please fix these issues manually and run the script again")

    print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
    print("1. Review the changes with: git diff")
    print("2. Run tests: poetry run pytest")
    print("3. Run full CI check: python scripts/run_ci_locally.py")
    print(
        "4. Commit your changes: git add . && git commit -m 'Fix code quality issues'"
    )

    sys.exit(0 if all_fixed else 1)


if __name__ == "__main__":
    main()
