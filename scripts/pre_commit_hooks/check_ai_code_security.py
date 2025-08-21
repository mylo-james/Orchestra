#!/usr/bin/env python3
"""
AI Code Generation Security Hook
Validates generated code for security vulnerabilities and dangerous patterns.
"""

import ast
import sys
import argparse
import subprocess
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Set


class AICodeSecurityScanner:
    """Comprehensive security scanning for AI-generated code."""
    
    # Dangerous operations that should be flagged
    BLOCKED_OPERATIONS = {
        'file_system': [
            'os.remove', 'os.unlink', 'os.rmdir', 'shutil.rmtree',
            'os.system', 'os.popen', 'os.spawn*', 'pathlib.Path.unlink'
        ],
        'network': [
            'socket.socket', 'urllib.request', 'requests.get', 'requests.post',
            'http.client', 'ftplib', 'smtplib', 'telnetlib'
        ],
        'process': [
            'subprocess.run', 'subprocess.call', 'subprocess.Popen',
            'os.exec*', 'multiprocessing.Process', 'threading.Thread'
        ],
        'dynamic_execution': [
            'eval(', 'exec(', '__import__', 'compile(', 'globals()', 'locals()',
            'getattr(', 'setattr(', 'delattr(', 'hasattr('
        ],
        'file_operations': [
            'open(', 'file(', 'input(', 'raw_input('
        ]
    }
    
    # Allowed imports for AI agents (whitelist approach)
    ALLOWED_IMPORTS = {
        'openai', 'pydantic', 'typing', 'dataclasses', 'enum',
        'datetime', 'uuid', 'json', 'logging', 'pathlib',
        'temporal', 'pinecone', 'numpy', 'pandas',
        'fastapi', 'starlette', 'uvicorn',
        'pytest', 'unittest', 'mock'
    }
    
    # Suspicious string patterns
    SUSPICIOUS_PATTERNS = [
        r'password.*=.*["\'].*["\']',
        r'api_key.*=.*["\'].*["\']',
        r'secret.*=.*["\'].*["\']',
        r'token.*=.*["\'].*["\']',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__.*__\s*=',  # Dunder method assignments
    ]

    def __init__(self):
        self.issues = []
        
    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Main scanning entry point."""
        self.issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError) as e:
            return [{"type": "ERROR", "message": f"Cannot read file: {e}"}]
        
        # Parse AST for structural analysis
        try:
            tree = ast.parse(content)
            self._analyze_ast_security(tree, file_path)
        except SyntaxError as e:
            self.issues.append({
                "type": "SYNTAX_ERROR",
                "line": e.lineno,
                "message": f"Syntax error: {e.msg}"
            })
            return self.issues
        
        # Pattern-based scanning
        self._scan_dangerous_patterns(content, file_path)
        
        # Run Bandit if available
        self._run_bandit_scan(file_path)
        
        return self.issues

    def _analyze_ast_security(self, tree: ast.AST, file_path: Path):
        """Analyze AST for security issues."""
        
        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self, scanner):
                self.scanner = scanner
                
            def visit_Call(self, node):
                """Check function calls for dangerous operations."""
                func_name = self._get_call_name(node)
                
                # Check against blocked operations
                for category, operations in self.scanner.BLOCKED_OPERATIONS.items():
                    for op in operations:
                        if func_name and op in func_name:
                            self.scanner.issues.append({
                                "type": "DANGEROUS_CALL",
                                "line": node.lineno,
                                "category": category,
                                "message": f"Dangerous operation detected: {func_name}"
                            })
                
                self.generic_visit(node)
                
            def visit_Import(self, node):
                """Check imports for unauthorized modules."""
                for alias in node.names:
                    if not self._is_allowed_import(alias.name):
                        self.scanner.issues.append({
                            "type": "UNAUTHORIZED_IMPORT",
                            "line": node.lineno,
                            "message": f"Unauthorized import: {alias.name}"
                        })
                self.generic_visit(node)
                
            def visit_ImportFrom(self, node):
                """Check from imports for unauthorized modules."""
                if node.module and not self._is_allowed_import(node.module):
                    self.scanner.issues.append({
                        "type": "UNAUTHORIZED_IMPORT",
                        "line": node.lineno,
                        "message": f"Unauthorized import from: {node.module}"
                    })
                self.generic_visit(node)
                
            def _get_call_name(self, node):
                """Extract function call name."""
                if isinstance(node.func, ast.Name):
                    return node.func.id
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        return f"{node.func.value.id}.{node.func.attr}"
                return None
                
            def _is_allowed_import(self, module_name: str) -> bool:
                """Check if import is in whitelist."""
                if not module_name:
                    return True
                    
                # Check against allowed imports
                base_module = module_name.split('.')[0]
                return base_module in self.scanner.ALLOWED_IMPORTS
        
        visitor = SecurityVisitor(self)
        visitor.visit(tree)

    def _scan_dangerous_patterns(self, content: str, file_path: Path):
        """Scan for dangerous string patterns."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append({
                        "type": "SUSPICIOUS_PATTERN",
                        "line": line_num,
                        "message": f"Suspicious pattern detected: {pattern}"
                    })

    def _run_bandit_scan(self, file_path: Path):
        """Run Bandit security scanner if available."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                result = subprocess.run(
                    ['bandit', '-f', 'json', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout:
                    bandit_results = json.loads(result.stdout)
                    for issue in bandit_results.get('results', []):
                        self.issues.append({
                            "type": "BANDIT_SECURITY",
                            "line": issue.get('line_number', 0),
                            "severity": issue.get('issue_severity', 'UNKNOWN'),
                            "message": f"Bandit: {issue.get('issue_text', 'Security issue')}"
                        })
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            # Bandit not available or failed - continue without it
            pass


def main():
    parser = argparse.ArgumentParser(description="Check for AI prompt injection and code security")
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args()
    
    scanner = AICodeSecurityScanner()
    exit_code = 0
    total_issues = 0
    
    for filename in args.filenames:
        file_path = Path(filename)
        
        # Skip non-Python files for code analysis
        if file_path.suffix not in ['.py', '.md', '.txt', '.json']:
            continue
            
        print(f"🔍 Scanning {filename} for AI security issues...")
        
        issues = scanner.scan_file(file_path)
        
        if issues:
            print(f"⚠️  Found {len(issues)} security issues in {filename}:")
            for issue in issues:
                line_info = f":{issue.get('line', '?')}" if issue.get('line') else ""
                severity = issue.get('severity', 'HIGH')
                print(f"  ❌ {filename}{line_info} [{issue['type']}] [{severity}] {issue['message']}")
            
            total_issues += len(issues)
            
            # Critical issues fail the hook
            critical_types = ['DANGEROUS_CALL', 'UNAUTHORIZED_IMPORT', 'SYNTAX_ERROR']
            if any(issue['type'] in critical_types for issue in issues):
                exit_code = 1
    
    if total_issues == 0:
        print("✅ No AI security issues detected")
    else:
        print(f"\n🚨 SECURITY SUMMARY: Found {total_issues} total issues")
        if exit_code == 1:
            print("❌ Critical security issues detected - commit blocked!")
            print("🛠️  Please fix critical issues before committing.")
        else:
            print("⚠️  Non-critical issues detected - please review.")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())