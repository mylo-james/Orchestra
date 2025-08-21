#!/usr/bin/env python3
"""
Prompt Template Validation Script
Validates prompt templates for safety and injection resistance.
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple


class PromptTemplateValidator:
    """Validates prompt templates for AI safety."""
    
    # Dangerous template patterns
    DANGEROUS_PATTERNS = [
        # Direct user input insertion without validation
        (r'\{.*user.*input.*\}', "Direct user input insertion"),
        (r'f".*\{.*user.*\}"', "F-string with user input"),
        (r'\.format\(.*user.*\)', "String format with user input"),
        
        # System prompt manipulation
        (r'\{.*\}.*system', "User input before system prompt"),
        (r'system.*\{.*\}', "User input in system prompt"),
        
        # Role confusion
        (r'role.*\{.*\}', "Dynamic role assignment"),
        (r'\{.*\}.*assistant', "User input affecting assistant role"),
        
        # Instruction override vectors
        (r'instructions.*\{.*\}', "User input in instructions"),
        (r'\{.*\}.*ignore', "User input with ignore patterns"),
    ]
    
    # Safe template patterns
    SAFE_PATTERNS = [
        r'\{validated_input\}',      # Validated input
        r'\{sanitized_.*\}',         # Sanitized variables
        r'\{safe_.*\}',             # Safe variables
        r'\{config\..*\}',          # Configuration variables
    ]
    
    # Required safety measures in templates
    REQUIRED_SAFETY_MEASURES = [
        'input validation',
        'sanitization', 
        'length limits',
        'content filtering'
    ]

    def __init__(self):
        self.issues = []

    def validate_prompt_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate a prompt template file."""
        self.issues = []
        
        print(f"📝 Validating prompt template: {file_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError) as e:
            return [{"type": "READ_ERROR", "message": f"Cannot read {file_path}: {e}"}]
        
        # 1. Check for dangerous patterns
        self._check_dangerous_patterns(content, file_path)
        
        # 2. Validate template structure
        self._validate_template_structure(content, file_path)
        
        # 3. Check for safety documentation
        self._check_safety_documentation(content, file_path)
        
        # 4. Validate variable usage
        self._validate_variable_usage(content, file_path)
        
        return self.issues

    def _check_dangerous_patterns(self, content: str, file_path: Path):
        """Check for dangerous template patterns."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's mitigated by safe patterns
                    is_safe = any(re.search(safe_pattern, line, re.IGNORECASE) 
                                for safe_pattern, _ in self.SAFE_PATTERNS)
                    
                    if not is_safe:
                        self.issues.append({
                            "type": "DANGEROUS_TEMPLATE_PATTERN",
                            "line": line_num,
                            "pattern": description,
                            "severity": "HIGH",
                            "message": f"Dangerous template pattern: {description}"
                        })

    def _validate_template_structure(self, content: str, file_path: Path):
        """Validate overall template structure."""
        # Check for proper template sections
        required_sections = ['system', 'user', 'validation']
        content_lower = content.lower()
        
        missing_sections = []
        for section in required_sections:
            if section not in content_lower:
                missing_sections.append(section)
        
        if missing_sections:
            self.issues.append({
                "type": "MISSING_TEMPLATE_SECTIONS",
                "severity": "MEDIUM",
                "sections": missing_sections,
                "message": f"Template missing sections: {', '.join(missing_sections)}"
            })
        
        # Check template length
        if len(content) > 5000:
            self.issues.append({
                "type": "TEMPLATE_TOO_LONG",
                "severity": "MEDIUM",
                "length": len(content),
                "message": f"Template very long ({len(content)} chars) - consider breaking down"
            })

    def _check_safety_documentation(self, content: str, file_path: Path):
        """Check for safety documentation in template."""
        content_lower = content.lower()
        
        # Look for safety documentation
        safety_indicators = [
            'safety', 'security', 'validation', 'sanitization',
            'input filtering', 'content filtering'
        ]
        
        has_safety_docs = any(indicator in content_lower for indicator in safety_indicators)
        
        if not has_safety_docs:
            self.issues.append({
                "type": "MISSING_SAFETY_DOCUMENTATION",
                "severity": "HIGH",
                "message": "Template missing safety and security documentation"
            })

    def _validate_variable_usage(self, content: str, file_path: Path):
        """Validate how variables are used in templates."""
        # Find all template variables
        variables = re.findall(r'\{([^}]+)\}', content)
        
        for var in variables:
            var_clean = var.strip()
            
            # Check for direct user input variables
            if any(keyword in var_clean.lower() 
                  for keyword in ['user', 'input', 'raw', 'direct']):
                # Should be validated/sanitized
                if not any(safety in var_clean.lower() 
                          for safety in ['validated', 'sanitized', 'safe', 'filtered']):
                    self.issues.append({
                        "type": "UNSAFE_USER_INPUT_VARIABLE",
                        "variable": var_clean,
                        "severity": "HIGH",
                        "message": f"Unsafe user input variable: {var_clean} (should be validated/sanitized)"
                    })
            
            # Check for system-level variables
            if any(keyword in var_clean.lower() 
                  for keyword in ['system', 'admin', 'root', 'config']):
                self.issues.append({
                    "type": "SYSTEM_VARIABLE_IN_TEMPLATE",
                    "variable": var_clean,
                    "severity": "MEDIUM",
                    "message": f"System variable in user template: {var_clean}"
                })

    def validate_prompt_directory(self, directory: Path) -> Dict[str, Any]:
        """Validate all prompt templates in a directory."""
        if not directory.exists():
            return {"success": True, "message": "No prompt directory found"}
        
        template_files = list(directory.rglob('*.prompt')) + list(directory.rglob('*.template'))
        
        if not template_files:
            return {"success": True, "message": "No prompt template files found"}
        
        all_issues = []
        for template_file in template_files:
            issues = self.validate_prompt_file(template_file)
            all_issues.extend(issues)
        
        critical_issues = [i for i in all_issues if i.get('severity') == 'CRITICAL']
        high_issues = [i for i in all_issues if i.get('severity') == 'HIGH']
        
        return {
            "success": len(critical_issues) == 0,
            "total_issues": len(all_issues),
            "critical_issues": len(critical_issues),
            "high_issues": len(high_issues),
            "issues": all_issues
        }


def main():
    parser = argparse.ArgumentParser(description="Validate prompt templates")
    parser.add_argument('files', nargs='*', help='Prompt template files to validate')
    parser.add_argument('--directory', help='Directory to scan for prompt templates')
    args = parser.parse_args()
    
    validator = PromptTemplateValidator()
    exit_code = 0
    
    if args.directory:
        # Validate entire directory
        result = validator.validate_prompt_directory(Path(args.directory))
        
        if not result['success']:
            print(f"❌ Found {result['total_issues']} issues in prompt templates")
            print(f"  Critical: {result['critical_issues']}")
            print(f"  High: {result['high_issues']}")
            exit_code = 1
        else:
            print("✅ All prompt templates validated successfully")
            
    elif args.files:
        # Validate specific files
        total_issues = 0
        
        for filename in args.files:
            file_path = Path(filename)
            
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                exit_code = 1
                continue
            
            issues = validator.validate_prompt_file(file_path)
            
            if issues:
                print(f"⚠️  Found {len(issues)} issues in {filename}:")
                for issue in issues:
                    line_info = f":{issue.get('line', '?')}" if issue.get('line') else ""
                    severity = issue.get('severity', 'MEDIUM')
                    print(f"  ❌ {filename}{line_info} [{issue['type']}] [{severity}] {issue['message']}")
                
                total_issues += len(issues)
                
                # Critical and high severity issues fail validation
                if any(issue.get('severity') in ['CRITICAL', 'HIGH'] for issue in issues):
                    exit_code = 1
            else:
                print(f"✅ {filename} - No issues found")
        
        if total_issues == 0:
            print(f"\n✅ All {len(args.files)} prompt templates validated successfully")
        else:
            print(f"\n📝 PROMPT VALIDATION SUMMARY: Found {total_issues} total issues")
            if exit_code == 1:
                print("❌ Critical prompt template issues detected!")
                print("🔧 Please fix issues before committing.")
    else:
        print("❌ No files or directory specified")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())