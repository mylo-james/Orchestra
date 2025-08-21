#!/usr/bin/env python3
"""
Final Security Check Hook
Comprehensive security validation before push to remote repository.
"""

import sys
import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set


class FinalSecurityChecker:
    """Performs comprehensive security validation before push."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []

    def run_comprehensive_check(self) -> bool:
        """Run all security checks."""
        print("🛡️ Running comprehensive security validation...")
        
        # 1. Check for secrets in entire repository
        self._check_secrets_scan()
        
        # 2. Validate all agent code
        self._validate_agent_security()
        
        # 3. Check dependencies for vulnerabilities
        self._check_dependency_security()
        
        # 4. Validate configuration files
        self._validate_config_security()
        
        # 5. Check for AI-specific security issues
        self._check_ai_security_patterns()
        
        # Report results
        return self._report_results()

    def _check_secrets_scan(self):
        """Comprehensive secrets scanning."""
        print("🔍 Scanning for secrets and credentials...")
        
        try:
            # Run detect-secrets
            result = subprocess.run([
                'detect-secrets', 'scan', '--all-files', '--baseline', '.secrets.baseline'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                self.issues.append({
                    "type": "SECRETS_DETECTED",
                    "severity": "CRITICAL",
                    "message": "Potential secrets detected in repository"
                })
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.warnings.append("Could not run secrets scan - ensure detect-secrets is installed")

    def _validate_agent_security(self):
        """Validate all agent files for security compliance."""
        print("🤖 Validating agent security...")
        
        agent_files = list(Path('src/agents').rglob('*.py')) if Path('src/agents').exists() else []
        
        for agent_file in agent_files:
            issues = self._scan_agent_file(agent_file)
            self.issues.extend(issues)

    def _scan_agent_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan individual agent file for security issues."""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return issues
        
        # Check for dangerous patterns
        dangerous_patterns = [
            (r'eval\s*\(', "Dynamic code execution"),
            (r'exec\s*\(', "Dynamic code execution"),
            (r'os\.system\s*\(', "System command execution"),
            (r'subprocess\..*shell=True', "Shell command injection risk"),
            (r'__import__\s*\(', "Dynamic import"),
            (r'open\s*\([^)]*["\'][rwa]', "File operations without validation"),
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "type": "DANGEROUS_PATTERN",
                        "file": str(file_path),
                        "line": line_num,
                        "severity": "HIGH",
                        "pattern": description,
                        "message": f"{description} detected in agent code"
                    })
        
        return issues

    def _check_dependency_security(self):
        """Check dependencies for known vulnerabilities."""
        print("📦 Checking dependency security...")
        
        try:
            # Run safety check
            result = subprocess.run([
                'poetry', 'run', 'safety', 'check', '--json'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0 and result.stdout:
                try:
                    safety_data = json.loads(result.stdout)
                    for vuln in safety_data:
                        self.issues.append({
                            "type": "VULNERABLE_DEPENDENCY",
                            "severity": "HIGH",
                            "package": vuln.get('package_name', 'unknown'),
                            "vulnerability": vuln.get('vulnerability_id', 'unknown'),
                            "message": f"Vulnerable dependency: {vuln.get('package_name')} - {vuln.get('advisory')}"
                        })
                except json.JSONDecodeError:
                    pass
                    
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.warnings.append("Could not run dependency security check")

    def _validate_config_security(self):
        """Validate configuration files for security issues."""
        print("⚙️ Validating configuration security...")
        
        config_files = [
            '.env.example',
            'pyproject.toml',
            'docker-compose.yml',
            'Dockerfile'
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                self._scan_config_file(Path(config_file))

    def _scan_config_file(self, file_path: Path):
        """Scan configuration file for security issues."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, description in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's clearly a template (contains placeholder text)
                    if any(placeholder in line.lower() 
                          for placeholder in ['your_', 'example_', 'placeholder', 'xxx']):
                        continue
                        
                    self.issues.append({
                        "type": "HARDCODED_SECRET",
                        "file": str(file_path),
                        "line": line_num,
                        "severity": "CRITICAL",
                        "pattern": description,
                        "message": f"{description} in configuration file"
                    })

    def _check_ai_security_patterns(self):
        """Check for AI-specific security patterns across the codebase."""
        print("🤖 Checking AI-specific security patterns...")
        
        # Find all Python files
        python_files = list(Path('.').rglob('*.py'))
        
        ai_security_patterns = [
            (r'openai\.api_key\s*=', "Direct API key assignment"),
            (r'client\s*=\s*OpenAI\([^)]*api_key\s*=\s*["\']', "Hardcoded OpenAI API key"),
            (r'prompt\s*=.*\+.*user.*input', "Unsafe prompt concatenation"),
            (r'f["\'].*\{.*user.*\}.*system', "Potential prompt injection vector"),
        ]
        
        for py_file in python_files:
            if py_file.name.startswith('.') or 'test' in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, description in ai_security_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.issues.append({
                                "type": "AI_SECURITY_RISK",
                                "file": str(py_file),
                                "line": line_num,
                                "severity": "HIGH",
                                "pattern": description,
                                "message": f"AI security risk: {description}"
                            })
                            
            except (UnicodeDecodeError, PermissionError):
                continue

    def _report_results(self) -> bool:
        """Report security check results."""
        critical_issues = [issue for issue in self.issues if issue.get('severity') == 'CRITICAL']
        high_issues = [issue for issue in self.issues if issue.get('severity') == 'HIGH']
        
        if self.warnings:
            print("\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        
        if not self.issues:
            print("\n✅ All security checks passed!")
            return True
        
        print(f"\n🛡️ SECURITY SUMMARY:")
        print(f"  Critical issues: {len(critical_issues)}")
        print(f"  High severity issues: {len(high_issues)}")
        print(f"  Total issues: {len(self.issues)}")
        
        # Show all issues
        for issue in self.issues:
            severity = issue.get('severity', 'MEDIUM')
            file_info = f"{issue.get('file', '')}:{issue.get('line', '')}" if issue.get('file') else ""
            print(f"  ❌ [{severity}] {file_info} {issue['message']}")
        
        if critical_issues:
            print("\n❌ CRITICAL SECURITY ISSUES DETECTED - PUSH BLOCKED!")
            print("🔒 Please fix all critical security issues before pushing.")
            return False
        elif high_issues:
            print("\n⚠️  HIGH SEVERITY ISSUES DETECTED")
            print("🔍 Please review and fix high severity issues.")
            # Allow push but warn
            return True
        else:
            print("\n✅ No critical security issues - push allowed")
            return True


def main():
    """Main entry point for final security check."""
    checker = FinalSecurityChecker()
    
    # Run comprehensive security check
    passed = checker.run_comprehensive_check()
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())