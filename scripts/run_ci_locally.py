#!/usr/bin/env python3
"""Script to run CI checks locally before pushing to GitHub."""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str) -> None:
    """Print a colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def run_command(command: List[str], description: str, allow_failure: bool = False) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print_info(f"Running: {description}")
    print(f"{Colors.CYAN}Command: {' '.join(command)}{Colors.END}")

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            print_success(f"{description} completed in {duration:.2f}s")
            if result.stdout.strip():
                print(f"{Colors.WHITE}{result.stdout.strip()}{Colors.END}")
            return True, result.stdout
        else:
            if allow_failure:
                print_warning(f"{description} failed (allowed) in {duration:.2f}s")
            else:
                print_error(f"{description} failed in {duration:.2f}s")

            if result.stderr.strip():
                print(f"{Colors.RED}STDERR: {result.stderr.strip()}{Colors.END}")
            if result.stdout.strip():
                print(f"{Colors.YELLOW}STDOUT: {result.stdout.strip()}{Colors.END}")

            return allow_failure, result.stderr

    except FileNotFoundError:
        print_error(f"Command not found: {command[0]}")
        return False, f"Command not found: {command[0]}"
    except Exception as e:
        print_error(f"Error running {description}: {e}")
        return False, str(e)


def check_prerequisites() -> bool:
    """Check that required tools are available."""
    print_header("Checking Prerequisites")

    required_tools = [
        (["poetry", "--version"], "Poetry"),
        (["python", "--version"], "Python"),
        (["git", "--version"], "Git"),
    ]

    all_good = True
    for command, tool in required_tools:
        success, _ = run_command(command, f"Check {tool}", allow_failure=True)
        if not success:
            print_error(f"{tool} is not available")
            all_good = False

    return all_good


def setup_environment() -> bool:
    """Set up the test environment."""
    print_header("Setting Up Environment")

    # Check if .env exists, create from .env.example if not
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        print_info("Creating .env from .env.example")
        env_file.write_text(env_example.read_text())

        # Add test values
        with env_file.open("a") as f:
            f.write("\n# Test values added by CI script\n")
            f.write("ENVIRONMENT=test\n")
            f.write("DEBUG=true\n")
            f.write("OPENAI_API_KEY=sk-test-key-for-local-ci-testing\n")
            f.write("PINECONE_API_KEY=test-pinecone-key\n")
            f.write("PINECONE_ENVIRONMENT=test-environment\n")

        print_success("Created .env with test values")

    # Install dependencies
    success, _ = run_command(
        ["poetry", "install"],
        "Install dependencies"
    )

    return success


def run_code_quality_checks() -> Dict[str, bool]:
    """Run code quality checks."""
    print_header("Code Quality Checks")

    checks = {}

    # Black formatting check
    checks["black"] = run_command(
        ["poetry", "run", "black", "--check", "src/", "tests/"],
        "Black formatting check",
        allow_failure=True
    )[0]

    # isort import sorting check
    checks["isort"] = run_command(
        ["poetry", "run", "isort", "--check-only", "src/", "tests/"],
        "isort import sorting check",
        allow_failure=True
    )[0]

    # Ruff linting
    checks["ruff"] = run_command(
        ["poetry", "run", "ruff", "check", "src/", "tests/"],
        "Ruff linting",
        allow_failure=True
    )[0]

    # MyPy type checking
    checks["mypy"] = run_command(
        ["poetry", "run", "mypy", "src/"],
        "MyPy type checking",
        allow_failure=True
    )[0]

    # Pre-commit hooks
    checks["pre-commit"] = run_command(
        ["poetry", "run", "pre-commit", "run", "--all-files"],
        "Pre-commit hooks",
        allow_failure=True
    )[0]

    return checks


def run_security_checks() -> Dict[str, bool]:
    """Run security checks."""
    print_header("Security Checks")

    checks = {}

    # Bandit security scan
    checks["bandit"] = run_command(
        ["poetry", "run", "bandit", "-r", "src/", "-c", "bandit.yaml"],
        "Bandit security scan",
        allow_failure=True
    )[0]

    # Safety dependency check
    checks["safety"] = run_command(
        ["poetry", "run", "safety", "check"],
        "Safety dependency check",
        allow_failure=True
    )[0]

    return checks


def run_tests() -> Dict[str, bool]:
    """Run the test suite."""
    print_header("Test Suite")

    tests = {}

    # Unit tests
    tests["unit"] = run_command(
        ["poetry", "run", "pytest", "tests/unit/", "-v", "--tb=short"],
        "Unit tests",
        allow_failure=True
    )[0]

    # Integration tests
    tests["integration"] = run_command(
        ["poetry", "run", "pytest", "tests/integration/", "-v", "--tb=short"],
        "Integration tests",
        allow_failure=True
    )[0]

    # Security tests
    tests["security"] = run_command(
        ["poetry", "run", "pytest", "tests/security/", "-v", "--tb=short"],
        "Security tests",
        allow_failure=True
    )[0]

    # Coverage report
    tests["coverage"] = run_command(
        ["poetry", "run", "pytest", "tests/", "--cov=src", "--cov-report=term-missing", "--cov-report=html"],
        "Coverage report",
        allow_failure=True
    )[0]

    return tests


def run_docker_checks() -> Dict[str, bool]:
    """Run Docker-related checks."""
    print_header("Docker Checks")

    checks = {}

    # Check if Docker is available
    docker_available, _ = run_command(
        ["docker", "--version"],
        "Check Docker availability",
        allow_failure=True
    )

    if not docker_available:
        print_warning("Docker not available, skipping Docker checks")
        return {"docker": False}

    # Build Docker image
    checks["build"] = run_command(
        ["docker", "build", "-t", "orchestra:local-ci", "."],
        "Build Docker image",
        allow_failure=True
    )[0]

    if checks["build"]:
        # Test Docker image
        checks["test"] = run_command(
            ["docker", "run", "--rm", "orchestra:local-ci", "python", "-c", "import src; print('Docker image works!')"],
            "Test Docker image",
            allow_failure=True
        )[0]
    else:
        checks["test"] = False

    return checks


def print_summary(results: Dict[str, Dict[str, bool]]) -> bool:
    """Print a summary of all results."""
    print_header("Summary")

    all_passed = True
    total_checks = 0
    passed_checks = 0

    for category, checks in results.items():
        if not checks:  # Skip empty categories
            continue

        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{category.upper()}:{Colors.END}")

        for check_name, passed in checks.items():
            total_checks += 1
            if passed:
                passed_checks += 1
                print_success(f"{check_name}")
            else:
                print_error(f"{check_name}")
                all_passed = False

    print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
    print(f"Passed: {passed_checks}/{total_checks}")

    if all_passed:
        print_success("All checks passed! ✨")
    else:
        print_error(f"Some checks failed. Please fix issues before pushing.")

    return all_passed


def main():
    """Main function to run all CI checks locally."""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("🎼 Orchestra Local CI Runner")
    print("Running the same checks that will run in GitHub Actions")
    print(f"{Colors.END}")

    start_time = time.time()

    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed")
        sys.exit(1)

    # Setup environment
    if not setup_environment():
        print_error("Environment setup failed")
        sys.exit(1)

    # Run all checks
    results = {
        "Code Quality": run_code_quality_checks(),
        "Security": run_security_checks(),
        "Tests": run_tests(),
        "Docker": run_docker_checks(),
    }

    # Print summary
    total_time = time.time() - start_time
    success = print_summary(results)

    print(f"\n{Colors.BOLD}Total time: {total_time:.2f}s{Colors.END}")

    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Ready to push! All checks passed.{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}💥 Fix issues before pushing.{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()