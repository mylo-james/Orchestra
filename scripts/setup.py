#!/usr/bin/env python3
"""Setup script for Orchestra development environment."""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if check and result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)

    return result


def check_prerequisites():
    """Check that required tools are installed."""
    print("🔍 Checking prerequisites...")

    required_tools = {
        "python3": "Python 3.12+",
        "poetry": "Poetry 1.7.1+",
        "docker": "Docker",
    }

    missing_tools = []

    for tool, description in required_tools.items():
        result = run_command(f"which {tool}", check=False)
        if result.returncode != 0:
            missing_tools.append(f"{tool} ({description})")

    if missing_tools:
        print("❌ Missing required tools:")
        for tool in missing_tools:
            print(f"  - {tool}")
        print("\nPlease install the missing tools and run this script again.")
        sys.exit(1)

    print("✅ All prerequisites are installed")


def setup_environment():
    """Setup the development environment."""
    print("🔧 Setting up environment...")

    # Check if .env exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("📋 Copying .env.example to .env")
            run_command("cp .env.example .env")
            print("⚠️  Please edit .env with your actual API keys and configuration")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file already exists")

    return True


def install_dependencies():
    """Install Python dependencies using Poetry."""
    print("📦 Installing Python dependencies...")

    # Install dependencies
    run_command("poetry install")

    # Install pre-commit hooks
    print("🪝 Installing pre-commit hooks...")
    run_command("poetry run pre-commit install")

    print("✅ Dependencies installed successfully")


def setup_docker():
    """Setup Docker environment."""
    print("🐳 Setting up Docker environment...")

    # Check if Docker is running
    result = run_command("docker info", check=False)
    if result.returncode != 0:
        print(
            "❌ Docker is not running. Please start Docker and run this script again."
        )
        return False

    # Build Docker images
    print("🏗️  Building Docker images...")
    run_command("docker compose build")

    # Start services
    print("🚀 Starting services...")
    run_command("docker compose up -d")

    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    import time

    time.sleep(10)

    # Check service status
    result = run_command("docker compose ps", check=False)
    print(result.stdout)

    print("✅ Docker environment setup complete")
    return True


def run_health_check():
    """Run system health check."""
    print("🏥 Running health check...")

    # Run Orchestra health check
    result = run_command("poetry run python -m orchestra.cli.main health", check=False)

    if result.returncode == 0:
        print("✅ Health check passed")
        return True
    else:
        print("❌ Health check failed")
        print(result.stdout)
        print(result.stderr)
        return False


def run_tests():
    """Run basic tests to verify setup."""
    print("🧪 Running basic tests...")

    # Run unit tests
    result = run_command("poetry run pytest tests/unit/ -v", check=False)

    if result.returncode == 0:
        print("✅ Basic tests passed")
        return True
    else:
        print("❌ Some tests failed")
        print(result.stdout)
        print(result.stderr)
        return False


def main():
    """Main setup function."""
    print("🎼 Orchestra Development Environment Setup")
    print("=" * 50)

    try:
        # Check prerequisites
        check_prerequisites()

        # Setup environment
        if not setup_environment():
            print("❌ Environment setup failed")
            return

        # Install dependencies
        install_dependencies()

        # Setup Docker
        if not setup_docker():
            print("❌ Docker setup failed")
            return

        # Run health check
        if not run_health_check():
            print("⚠️  Health check failed - you may need to configure API keys in .env")

        # Run tests
        if not run_tests():
            print("⚠️  Some tests failed - this may be due to missing API keys")

        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env with your API keys and configuration")
        print("2. Run: poetry run orchestra health")
        print("3. Run: poetry run orchestra --help")
        print("4. Check the README.md for detailed usage instructions")

    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
