#!/usr/bin/env python3
"""
Test Existence Check Hook
Ensures that test files exist for all new source files.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any


class TestExistenceChecker:
    """Checks that appropriate test files exist for source files."""
    
    # File patterns that require tests
    REQUIRES_TESTS = [
        'src/agents/**/*.py',
        'src/workflows/**/*.py', 
        'src/services/**/*.py',
        'src/security/**/*.py'
    ]
    
    # Files that don't need tests
    SKIP_PATTERNS = [
        '__init__.py',
        'config.py',
        'settings.py',
        'constants.py'
    ]

    def check_test_existence(self, source_files: List[str]) -> List[Dict[str, Any]]:
        """Check if test files exist for source files."""
        issues = []
        
        for file_path in source_files:
            if not self._should_have_test(file_path):
                continue
                
            test_paths = self._generate_test_paths(file_path)
            test_exists = any(Path(test_path).exists() for test_path in test_paths)
            
            if not test_exists:
                severity = self._get_test_severity(file_path)
                issues.append({
                    "type": "MISSING_TEST",
                    "file": file_path,
                    "severity": severity,
                    "expected_paths": test_paths,
                    "message": f"No test file found for {file_path}"
                })
        
        return issues

    def _should_have_test(self, file_path: str) -> bool:
        """Determine if a file should have tests."""
        path = Path(file_path)
        
        # Skip non-Python files
        if path.suffix != '.py':
            return False
            
        # Skip files in skip patterns
        if any(pattern in path.name for pattern in self.SKIP_PATTERNS):
            return False
            
        # Check if file is in a directory that requires tests
        return any(part in ['agents', 'workflows', 'services', 'security'] 
                  for part in path.parts)

    def _generate_test_paths(self, source_file: str) -> List[str]:
        """Generate possible test file paths."""
        source_path = Path(source_file)
        
        # Remove 'src/' prefix
        if source_path.parts[0] == 'src':
            relative_path = Path(*source_path.parts[1:])
        else:
            relative_path = source_path
            
        stem = relative_path.stem
        parent = relative_path.parent
        
        # Generate multiple possible test locations
        test_paths = [
            f"tests/unit/{parent}/test_{stem}.py",
            f"tests/unit/{parent}/{stem}_test.py", 
            f"tests/integration/{parent}/test_{stem}.py",
            f"tests/integration/{parent}/{stem}_test.py",
            f"tests/{parent}/test_{stem}.py"
        ]
        
        return test_paths

    def _get_test_severity(self, file_path: str) -> str:
        """Get severity level for missing tests."""
        path_parts = Path(file_path).parts
        
        if any(part in ['agents', 'security'] for part in path_parts):
            return "CRITICAL"
        elif any(part in ['workflows', 'services'] for part in path_parts):
            return "HIGH"
        else:
            return "MEDIUM"


def main():
    parser = argparse.ArgumentParser(description="Check that test files exist")
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args()
    
    if not args.filenames:
        print("✅ No files to check")
        return 0
    
    checker = TestExistenceChecker()
    issues = checker.check_test_existence(args.filenames)
    
    if not issues:
        print("✅ All source files have corresponding tests")
        return 0
    
    print(f"🧪 TEST EXISTENCE SUMMARY: Found {len(issues)} missing test files")
    
    critical_count = 0
    for issue in issues:
        severity = issue.get('severity', 'MEDIUM')
        file_path = issue['file']
        
        print(f"  ❌ {file_path} [{severity}] {issue['message']}")
        print(f"     Expected test locations:")
        for test_path in issue['expected_paths']:
            exists_marker = "✅" if Path(test_path).exists() else "❌"
            print(f"       {exists_marker} {test_path}")
        print()
        
        if severity == "CRITICAL":
            critical_count += 1
    
    if critical_count > 0:
        print(f"❌ {critical_count} critical modules missing tests - commit blocked!")
        print("🧪 Please create test files for critical modules before committing.")
        return 1
    else:
        print("⚠️  Some test files missing - consider adding tests for better coverage.")
        return 0


if __name__ == "__main__":
    sys.exit(main())