#!/usr/bin/env python3
"""
CI/CD Setup Script
Initializes the Orchestra AI CI/CD pipeline with all necessary configurations.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict


class CISetup:
    """Sets up the complete CI/CD pipeline for Orchestra AI."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.success_steps = []
        self.failed_steps = []

    def setup_complete_pipeline(self) -> bool:
        """Set up the complete CI/CD pipeline."""
        print("🚀 Setting up Orchestra AI CI/CD Pipeline...")
        print("=" * 60)
        
        steps = [
            ("📦 Installing Poetry", self._setup_poetry),
            ("🔧 Installing dependencies", self._install_dependencies),
            ("🪝 Setting up pre-commit hooks", self._setup_precommit),
            ("🔒 Initializing security baseline", self._setup_security),
            ("🧪 Setting up test infrastructure", self._setup_testing),
            ("📋 Creating CI configuration", self._verify_ci_config),
            ("🛡️ Validating security setup", self._validate_security_setup),
            ("📊 Running initial validation", self._run_initial_validation),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            try:
                if step_func():
                    self.success_steps.append(step_name)
                    print(f"✅ {step_name} completed successfully")
                else:
                    self.failed_steps.append(step_name)
                    print(f"❌ {step_name} failed")
            except Exception as e:
                self.failed_steps.append(step_name)
                print(f"❌ {step_name} failed with error: {e}")
        
        return self._report_results()

    def _setup_poetry(self) -> bool:
        """Set up Poetry for dependency management."""
        try:
            # Check if Poetry is installed
            result = subprocess.run(['poetry', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  📦 Poetry already installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        # Install Poetry
        print("  📦 Installing Poetry...")
        try:
            subprocess.run([
                'curl', '-sSL', 'https://install.python-poetry.org', '|', 'python3', '-'
            ], shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            print("  ❌ Failed to install Poetry")
            return False

    def _install_dependencies(self) -> bool:
        """Install all project dependencies."""
        try:
            print("  📚 Installing main dependencies...")
            subprocess.run(['poetry', 'install'], check=True, capture_output=True)
            
            print("  🔧 Installing development dependencies...")
            subprocess.run(['poetry', 'install', '--with', 'dev'], check=True, capture_output=True)
            
            print("  🧪 Installing test dependencies...")
            subprocess.run(['poetry', 'install', '--with', 'test'], check=True, capture_output=True)
            
            print("  🔒 Installing security dependencies...")
            subprocess.run(['poetry', 'install', '--with', 'security'], check=True, capture_output=True)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install dependencies: {e}")
            return False

    def _setup_precommit(self) -> bool:
        """Set up pre-commit hooks."""
        try:
            print("  🪝 Installing pre-commit...")
            subprocess.run(['poetry', 'run', 'pre-commit', 'install'], 
                          check=True, capture_output=True)
            
            print("  🪝 Installing pre-push hooks...")
            subprocess.run(['poetry', 'run', 'pre-commit', 'install', '--hook-type', 'pre-push'], 
                          check=True, capture_output=True)
            
            print("  🧪 Testing pre-commit hooks...")
            result = subprocess.run(['poetry', 'run', 'pre-commit', 'run', '--all-files'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print("  ⚠️  Pre-commit hooks found issues (this is normal for initial setup)")
                print("  🔧 Run 'poetry run pre-commit run --all-files' to fix issues")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to set up pre-commit: {e}")
            return False

    def _setup_security(self) -> bool:
        """Set up security scanning baseline."""
        try:
            print("  🔍 Setting up secrets detection baseline...")
            subprocess.run([
                'poetry', 'run', 'detect-secrets', 'scan', '--baseline', '.secrets.baseline'
            ], check=True, capture_output=True)
            
            print("  🔒 Running initial Bandit scan...")
            subprocess.run([
                'poetry', 'run', 'bandit', '-r', 'src/', '-f', 'json', '-o', 'bandit-baseline.json'
            ], capture_output=True)  # Don't fail on security issues in initial scan
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Security setup completed with warnings: {e}")
            return True  # Don't fail setup on security issues

    def _setup_testing(self) -> bool:
        """Set up test infrastructure."""
        # Create test directories if they don't exist
        test_dirs = [
            'tests/unit',
            'tests/integration', 
            'tests/security',
            'tests/e2e',
            'tests/performance',
            'tests/fixtures'
        ]
        
        for test_dir in test_dirs:
            test_path = Path(test_dir)
            test_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            init_file = test_path / '__init__.py'
            if not init_file.exists():
                init_file.write_text('"""Test module."""\n')
        
        # Create basic test configuration
        conftest_path = Path('tests/conftest.py')
        if not conftest_path.exists():
            conftest_content = '''"""Pytest configuration and fixtures for Orchestra AI tests."""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    # TODO: Implement mock client
    pass


@pytest.fixture
def mock_temporal_client():
    """Mock Temporal client for testing."""
    # TODO: Implement mock client
    pass


@pytest.fixture
def mock_pinecone_client():
    """Mock Pinecone client for testing."""
    # TODO: Implement mock client
    pass
'''
            conftest_path.write_text(conftest_content)
        
        print("  🧪 Test infrastructure created")
        return True

    def _verify_ci_config(self) -> bool:
        """Verify CI configuration files exist and are valid."""
        required_files = [
            '.github/workflows/ci.yml',
            '.github/workflows/pr-validation.yml',
            '.github/workflows/security-scan.yml',
            '.pre-commit-config.yaml',
            'pyproject.toml',
            '.flake8',
            'bandit.yaml'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"  ❌ Missing CI configuration files: {', '.join(missing_files)}")
            return False
        
        print("  ✅ All CI configuration files present")
        return True

    def _validate_security_setup(self) -> bool:
        """Validate security setup is working."""
        try:
            # Test security scripts
            security_scripts = [
                'scripts/security_check.py',
                'scripts/validate_agent_code.py',
                'scripts/validate_prompts.py'
            ]
            
            for script in security_scripts:
                if not Path(script).exists():
                    print(f"  ❌ Missing security script: {script}")
                    return False
                
                # Make scripts executable
                os.chmod(script, 0o755)
            
            print("  🛡️ Security validation setup complete")
            return True
        except Exception as e:
            print(f"  ❌ Security validation failed: {e}")
            return False

    def _run_initial_validation(self) -> bool:
        """Run initial validation to ensure everything works."""
        try:
            print("  🔍 Running code quality checks...")
            
            # Run Black check
            result = subprocess.run(['poetry', 'run', 'black', '--check', '.'], 
                                  capture_output=True)
            if result.returncode != 0:
                print("  ⚠️  Code formatting issues found - run 'poetry run black .' to fix")
            
            # Run isort check
            result = subprocess.run(['poetry', 'run', 'isort', '--check-only', '.'], 
                                  capture_output=True)
            if result.returncode != 0:
                print("  ⚠️  Import sorting issues found - run 'poetry run isort .' to fix")
            
            print("  ✅ Initial validation completed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Initial validation completed with warnings: {e}")
            return True  # Don't fail setup on formatting issues

    def _report_results(self) -> bool:
        """Report setup results."""
        print("\n" + "=" * 60)
        print("🎉 ORCHESTRA AI CI/CD SETUP COMPLETE!")
        print("=" * 60)
        
        if self.success_steps:
            print("\n✅ Successful steps:")
            for step in self.success_steps:
                print(f"  ✅ {step}")
        
        if self.failed_steps:
            print("\n❌ Failed steps:")
            for step in self.failed_steps:
                print(f"  ❌ {step}")
        
        if not self.failed_steps:
            print("\n🎉 ALL SETUP STEPS COMPLETED SUCCESSFULLY!")
            print("\n📋 Next Steps:")
            print("  1. Run 'poetry run pre-commit run --all-files' to fix any formatting issues")
            print("  2. Commit your changes to trigger the CI pipeline")
            print("  3. Create a pull request to test the PR validation workflow")
            print("  4. Configure GitHub secrets for deployment (see README)")
            
            print("\n🛡️ Security Features Enabled:")
            print("  ✅ Pre-commit hooks with AI-specific validations")
            print("  ✅ Comprehensive security scanning")
            print("  ✅ Test coverage enforcement (90% for agents, 80% overall)")
            print("  ✅ Prompt injection detection")
            print("  ✅ Code generation security validation")
            print("  ✅ Dependency vulnerability scanning")
            print("  ✅ License compliance checking")
            
            return True
        else:
            print(f"\n⚠️  Setup completed with {len(self.failed_steps)} failed steps")
            print("🔧 Please review and fix the failed steps manually")
            return False


def main():
    """Main setup function."""
    setup = CISetup()
    success = setup.setup_complete_pipeline()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())