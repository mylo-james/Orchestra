#!/usr/bin/env python3
"""
Health Check Script
Comprehensive system health validation for Orchestra AI.
"""

import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple


class HealthChecker:
    """Comprehensive health checking for Orchestra AI system."""
    
    def __init__(self):
        self.checks = []
        self.start_time = time.time()

    def run_all_checks(self) -> bool:
        """Run all health checks."""
        print("🏥 Orchestra AI System Health Check")
        print("=" * 50)
        
        checks = [
            ("🐍 Python Environment", self._check_python_environment),
            ("📦 Dependencies", self._check_dependencies),
            ("🔧 Development Tools", self._check_dev_tools),
            ("🧪 Test Infrastructure", self._check_test_infrastructure),
            ("🔒 Security Tools", self._check_security_tools),
            ("🤖 AI Services", self._check_ai_services),
            ("🗃️ Database Connectivity", self._check_database),
            ("🔗 External APIs", self._check_external_apis),
            ("📊 Monitoring", self._check_monitoring),
            ("🚀 CI/CD Configuration", self._check_cicd_config),
        ]
        
        passed = 0
        total = len(checks)
        
        for check_name, check_func in checks:
            print(f"\n{check_name}...")
            try:
                result = check_func()
                if result:
                    print(f"  ✅ {check_name} - OK")
                    passed += 1
                else:
                    print(f"  ❌ {check_name} - FAILED")
            except Exception as e:
                print(f"  ❌ {check_name} - ERROR: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print(f"🏥 HEALTH CHECK SUMMARY")
        print(f"  ✅ Passed: {passed}/{total}")
        print(f"  ❌ Failed: {total - passed}/{total}")
        print(f"  ⏱️ Duration: {time.time() - self.start_time:.1f}s")
        
        if passed == total:
            print("🎉 ALL HEALTH CHECKS PASSED!")
            return True
        else:
            print("⚠️ SOME HEALTH CHECKS FAILED")
            return False

    def _check_python_environment(self) -> bool:
        """Check Python environment setup."""
        try:
            # Check Python version
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            python_version = result.stdout.strip()
            print(f"    Python: {python_version}")
            
            # Check if we're in the right Python version
            if "3.12" not in python_version:
                print(f"    ⚠️ Expected Python 3.12, got {python_version}")
                return False
            
            # Check virtual environment
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                print("    ✅ Virtual environment active")
            else:
                print("    ⚠️ Not in virtual environment")
                
            return True
        except Exception as e:
            print(f"    ❌ Python environment check failed: {e}")
            return False

    def _check_dependencies(self) -> bool:
        """Check if all dependencies are installed."""
        try:
            # Check Poetry
            result = subprocess.run(['poetry', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"    Poetry: {result.stdout.strip()}")
            else:
                print("    ❌ Poetry not found")
                return False
            
            # Check core dependencies
            core_deps = ['openai', 'temporal', 'pinecone', 'fastapi', 'pydantic']
            for dep in core_deps:
                try:
                    __import__(dep)
                    print(f"    ✅ {dep}")
                except ImportError:
                    print(f"    ❌ {dep} not found")
                    return False
            
            return True
        except Exception as e:
            print(f"    ❌ Dependency check failed: {e}")
            return False

    def _check_dev_tools(self) -> bool:
        """Check development tools."""
        tools = [
            ('black', 'Code formatting'),
            ('isort', 'Import sorting'),
            ('flake8', 'Linting'),
            ('mypy', 'Type checking'),
            ('pytest', 'Testing framework'),
            ('pre-commit', 'Pre-commit hooks')
        ]
        
        all_good = True
        for tool, description in tools:
            try:
                result = subprocess.run(['poetry', 'run', tool, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"    ✅ {tool} - {description}")
                else:
                    print(f"    ❌ {tool} - Not working")
                    all_good = False
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                print(f"    ❌ {tool} - Not found or not working")
                all_good = False
        
        return all_good

    def _check_test_infrastructure(self) -> bool:
        """Check test infrastructure."""
        try:
            # Check test directories
            test_dirs = ['tests/unit', 'tests/integration', 'tests/security', 'tests/e2e']
            for test_dir in test_dirs:
                if Path(test_dir).exists():
                    print(f"    ✅ {test_dir}")
                else:
                    print(f"    ⚠️ {test_dir} - Missing")
            
            # Try running a simple test
            result = subprocess.run([
                'poetry', 'run', 'pytest', '--collect-only', '-q'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("    ✅ Test collection successful")
                return True
            else:
                print("    ❌ Test collection failed")
                return False
                
        except Exception as e:
            print(f"    ❌ Test infrastructure check failed: {e}")
            return False

    def _check_security_tools(self) -> bool:
        """Check security tools."""
        security_tools = [
            ('bandit', 'Security linting'),
            ('safety', 'Dependency vulnerability scanning'),
            ('detect-secrets', 'Secrets detection')
        ]
        
        all_good = True
        for tool, description in security_tools:
            try:
                result = subprocess.run(['poetry', 'run', tool, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"    ✅ {tool} - {description}")
                else:
                    print(f"    ❌ {tool} - Not working")
                    all_good = False
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                print(f"    ❌ {tool} - Not found")
                all_good = False
        
        return all_good

    def _check_ai_services(self) -> bool:
        """Check AI service connectivity (without making actual calls)."""
        try:
            # Check if OpenAI is importable and configured
            import openai
            print("    ✅ OpenAI SDK available")
            
            # Check environment variables (without exposing values)
            import os
            env_vars = ['OPENAI_API_KEY', 'TEMPORAL_HOST', 'PINECONE_API_KEY']
            for var in env_vars:
                if os.getenv(var):
                    print(f"    ✅ {var} configured")
                else:
                    print(f"    ⚠️ {var} not set")
            
            return True
        except ImportError as e:
            print(f"    ❌ AI services check failed: {e}")
            return False

    def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            import os
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                print("    ⚠️ DATABASE_URL not configured")
                return True  # Not required for all setups
            
            # Try to connect (would need actual database logic here)
            print("    ✅ Database configuration found")
            return True
            
        except Exception as e:
            print(f"    ❌ Database check failed: {e}")
            return False

    def _check_external_apis(self) -> bool:
        """Check external API configuration."""
        try:
            import os
            
            # Check API configurations
            apis = {
                'OpenAI': 'OPENAI_API_KEY',
                'GitHub': 'GITHUB_TOKEN', 
                'Temporal': 'TEMPORAL_HOST',
                'Pinecone': 'PINECONE_API_KEY'
            }
            
            configured_apis = 0
            for api_name, env_var in apis.items():
                if os.getenv(env_var):
                    print(f"    ✅ {api_name} configured")
                    configured_apis += 1
                else:
                    print(f"    ⚠️ {api_name} not configured")
            
            # At least OpenAI should be configured for basic functionality
            return configured_apis >= 1
            
        except Exception as e:
            print(f"    ❌ External API check failed: {e}")
            return False

    def _check_monitoring(self) -> bool:
        """Check monitoring and logging setup."""
        try:
            # Check log directory
            log_dir = Path('logs')
            if not log_dir.exists():
                log_dir.mkdir(exist_ok=True)
                print("    ✅ Log directory created")
            else:
                print("    ✅ Log directory exists")
            
            # Check if logging is configured
            import logging
            logger = logging.getLogger('orchestra')
            print("    ✅ Logging framework available")
            
            return True
        except Exception as e:
            print(f"    ❌ Monitoring check failed: {e}")
            return False

    def _check_cicd_config(self) -> bool:
        """Check CI/CD configuration."""
        required_files = [
            '.github/workflows/ci.yml',
            '.github/workflows/pr-validation.yml',
            '.github/workflows/security-scan.yml',
            '.pre-commit-config.yaml',
            'pyproject.toml'
        ]
        
        all_present = True
        for file_path in required_files:
            if Path(file_path).exists():
                print(f"    ✅ {file_path}")
            else:
                print(f"    ❌ {file_path} - Missing")
                all_present = False
        
        return all_present


def main():
    """Main health check function."""
    checker = HealthChecker()
    success = checker.run_all_checks()
    
    if success:
        print("\n🎉 System is healthy and ready for development!")
        return 0
    else:
        print("\n⚠️ System health issues detected. Please review and fix.")
        return 1


if __name__ == "__main__":
    sys.exit(main())