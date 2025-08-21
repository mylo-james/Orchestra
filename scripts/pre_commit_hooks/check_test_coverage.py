#!/usr/bin/env python3
"""
Test Coverage Enforcement Hook
Ensures adequate test coverage for all new and modified code.
"""

import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


class TestCoverageChecker:
    """Enforces test coverage requirements for Orchestra AI system."""
    
    # Coverage requirements by module type
    COVERAGE_REQUIREMENTS = {
        'agents': 95,      # AI agents need highest coverage
        'security': 100,   # Security code must be fully tested
        'workflows': 90,   # Temporal workflows need high coverage
        'services': 85,    # Business logic services
        'models': 80,      # Data models
        'utils': 75,       # Utility functions
        'default': 80      # Default requirement
    }
    
    # Critical modules that must have tests
    CRITICAL_MODULES = [
        'src/agents',
        'src/security',
        'src/workflows'
    ]

    def __init__(self):
        self.issues = []

    def check_coverage(self, changed_files: List[str]) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check test coverage for changed files."""
        python_files = [f for f in changed_files if f.endswith('.py') and f.startswith('src/')]
        
        if not python_files:
            return True, []
        
        print(f"📊 Checking test coverage for {len(python_files)} Python files...")
        
        # Run coverage on the specific files
        try:
            # First run tests to generate coverage
            subprocess.run([
                'poetry', 'run', 'pytest', 
                '--cov=src',
                '--cov-report=json',
                '--cov-report=term',
                'tests/unit/',
                '-q'
            ], check=True, capture_output=True)
            
            # Read coverage report
            coverage_data = self._read_coverage_report()
            
            # Check coverage for each changed file
            for file_path in python_files:
                self._check_file_coverage(file_path, coverage_data)
                
        except subprocess.CalledProcessError as e:
            self.issues.append({
                "type": "COVERAGE_ERROR",
                "message": f"Failed to run coverage analysis: {e}"
            })
            return False, self.issues
        
        # Check if any critical issues
        critical_issues = [issue for issue in self.issues 
                          if issue.get('severity') == 'CRITICAL']
        
        return len(critical_issues) == 0, self.issues

    def _read_coverage_report(self) -> Dict[str, Any]:
        """Read the coverage JSON report."""
        try:
            with open('coverage.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"files": {}}

    def _check_file_coverage(self, file_path: str, coverage_data: Dict[str, Any]):
        """Check coverage for a specific file."""
        # Normalize file path
        normalized_path = file_path.replace('\\', '/')
        
        # Find coverage data for this file
        file_coverage = None
        for covered_file, data in coverage_data.get('files', {}).items():
            if covered_file.endswith(normalized_path) or normalized_path.endswith(covered_file):
                file_coverage = data
                break
        
        if not file_coverage:
            # File not in coverage report - likely not tested
            module_type = self._get_module_type(file_path)
            if module_type in ['agents', 'security', 'workflows']:
                self.issues.append({
                    "type": "NO_COVERAGE",
                    "file": file_path,
                    "severity": "CRITICAL",
                    "message": f"Critical module {file_path} has no test coverage"
                })
            else:
                self.issues.append({
                    "type": "NO_COVERAGE",
                    "file": file_path,
                    "severity": "HIGH",
                    "message": f"File {file_path} has no test coverage"
                })
            return
        
        # Calculate coverage percentage
        summary = file_coverage.get('summary', {})
        covered_lines = summary.get('covered_lines', 0)
        num_statements = summary.get('num_statements', 1)
        coverage_percent = (covered_lines / num_statements) * 100 if num_statements > 0 else 0
        
        # Get required coverage for this module
        module_type = self._get_module_type(file_path)
        required_coverage = self.COVERAGE_REQUIREMENTS.get(module_type, 
                                                          self.COVERAGE_REQUIREMENTS['default'])
        
        if coverage_percent < required_coverage:
            severity = "CRITICAL" if module_type in ['agents', 'security'] else "HIGH"
            self.issues.append({
                "type": "INSUFFICIENT_COVERAGE",
                "file": file_path,
                "severity": severity,
                "coverage": round(coverage_percent, 1),
                "required": required_coverage,
                "message": f"Coverage {coverage_percent:.1f}% < required {required_coverage}%"
            })

    def _get_module_type(self, file_path: str) -> str:
        """Determine module type from file path."""
        path_parts = Path(file_path).parts
        
        for part in path_parts:
            if part in self.COVERAGE_REQUIREMENTS:
                return part
                
        return 'default'

    def check_test_files_exist(self, changed_files: List[str]) -> List[Dict[str, Any]]:
        """Check that test files exist for changed source files."""
        test_issues = []
        
        for file_path in changed_files:
            if not (file_path.endswith('.py') and file_path.startswith('src/')):
                continue
                
            # Skip __init__.py files
            if file_path.endswith('__init__.py'):
                continue
                
            # Generate expected test file paths
            expected_test_paths = self._generate_test_paths(file_path)
            
            # Check if any test file exists
            test_exists = any(Path(test_path).exists() for test_path in expected_test_paths)
            
            if not test_exists:
                module_type = self._get_module_type(file_path)
                severity = "CRITICAL" if module_type in ['agents', 'security'] else "HIGH"
                
                test_issues.append({
                    "type": "MISSING_TEST_FILE",
                    "file": file_path,
                    "severity": severity,
                    "expected_paths": expected_test_paths,
                    "message": f"No test file found for {file_path}"
                })
        
        return test_issues

    def _generate_test_paths(self, source_file: str) -> List[str]:
        """Generate possible test file paths for a source file."""
        source_path = Path(source_file)
        
        # Remove 'src/' prefix and get relative path
        relative_path = source_path.relative_to('src')
        
        # Generate test file names
        stem = relative_path.stem
        parent = relative_path.parent
        
        test_paths = [
            f"tests/unit/{parent}/test_{stem}.py",
            f"tests/unit/{parent}/{stem}_test.py",
            f"tests/integration/{parent}/test_{stem}.py",
            f"tests/{parent}/test_{stem}.py"
        ]
        
        return test_paths


def get_changed_files() -> List[str]:
    """Get list of changed files from git."""
    try:
        # Get staged files
        result = subprocess.run([
            'git', 'diff', '--cached', '--name-only'
        ], capture_output=True, text=True, check=True)
        
        return [line.strip() for line in result.stdout.split('\n') if line.strip()]
    except subprocess.CalledProcessError:
        return []


def main():
    parser = argparse.ArgumentParser(description="Check test coverage for changed files")
    parser.add_argument('filenames', nargs='*', help='Filenames to check (optional)')
    args = parser.parse_args()
    
    # Get changed files
    if args.filenames:
        changed_files = args.filenames
    else:
        changed_files = get_changed_files()
    
    if not changed_files:
        print("✅ No files to check for coverage")
        return 0
    
    checker = TestCoverageChecker()
    exit_code = 0
    
    # Check test coverage
    coverage_ok, coverage_issues = checker.check_coverage(changed_files)
    
    # Check test file existence
    test_file_issues = checker.check_test_files_exist(changed_files)
    
    all_issues = coverage_issues + test_file_issues
    
    if all_issues:
        print(f"📊 COVERAGE SUMMARY: Found {len(all_issues)} coverage issues")
        
        for issue in all_issues:
            severity = issue.get('severity', 'HIGH')
            file_info = issue.get('file', '')
            
            if issue['type'] == 'INSUFFICIENT_COVERAGE':
                print(f"  ❌ {file_info} [{severity}] {issue['message']}")
            elif issue['type'] == 'MISSING_TEST_FILE':
                print(f"  ❌ {file_info} [{severity}] {issue['message']}")
                print(f"     Expected test paths: {', '.join(issue['expected_paths'])}")
            else:
                print(f"  ❌ {file_info} [{severity}] {issue['message']}")
        
        # Fail on critical issues
        critical_issues = [issue for issue in all_issues if issue.get('severity') == 'CRITICAL']
        if critical_issues:
            exit_code = 1
            print(f"\n❌ {len(critical_issues)} critical coverage issues - commit blocked!")
            print("🧪 Please add tests for critical modules before committing.")
        else:
            print(f"\n⚠️  {len(all_issues)} coverage warnings - please consider adding tests.")
    else:
        print("✅ All coverage requirements met")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())