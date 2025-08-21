#!/usr/bin/env python3
"""
Agent Tool Validation Hook
Ensures all agent tools follow OpenAI SDK requirements and security standards.
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


class AgentToolValidator:
    """Validates agent tool functions for OpenAI SDK compliance and security."""
    
    REQUIRED_DOCSTRING_SECTIONS = [
        'description', 'parameters', 'returns'
    ]
    
    SECURITY_REQUIREMENTS = [
        'input_validation',
        'error_handling',
        'rate_limiting'
    ]

    def __init__(self):
        self.issues = []

    def validate_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate an agent file for tool compliance."""
        self.issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (UnicodeDecodeError, SyntaxError) as e:
            return [{"type": "PARSE_ERROR", "message": f"Cannot parse file: {e}"}]
        
        # Find agent tool functions
        tool_functions = self._find_tool_functions(tree)
        
        for func in tool_functions:
            self._validate_tool_function(func, content)
            
        return self.issues

    def _find_tool_functions(self, tree: ast.AST) -> List[ast.FunctionDef]:
        """Find functions that appear to be agent tools."""
        tool_functions = []
        
        class ToolFinder(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Check if function has tool-like characteristics
                if self._is_tool_function(node):
                    tool_functions.append(node)
                self.generic_visit(node)
                
            def _is_tool_function(self, node: ast.FunctionDef) -> bool:
                """Determine if a function is likely an agent tool."""
                # Check for tool decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id in ['tool', 'agent_tool']:
                            return True
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id in ['tool', 'agent_tool']:
                                return True
                
                # Check for tool-like naming patterns
                tool_keywords = ['tool', 'action', 'execute', 'perform', 'handle']
                func_name_lower = node.name.lower()
                if any(keyword in func_name_lower for keyword in tool_keywords):
                    return True
                    
                # Check if function is in agent classes
                return False
        
        finder = ToolFinder()
        finder.visit(tree)
        return tool_functions

    def _validate_tool_function(self, func: ast.FunctionDef, content: str):
        """Validate a single tool function."""
        func_name = func.name
        line_num = func.lineno
        
        # 1. Check for proper docstring
        docstring = ast.get_docstring(func)
        if not docstring:
            self.issues.append({
                "type": "MISSING_DOCSTRING",
                "line": line_num,
                "function": func_name,
                "message": "Tool function missing docstring"
            })
        else:
            self._validate_docstring(docstring, func_name, line_num)
        
        # 2. Check for type hints
        self._validate_type_hints(func, func_name, line_num)
        
        # 3. Check for security patterns
        self._validate_security_patterns(func, func_name, line_num)
        
        # 4. Check for error handling
        self._validate_error_handling(func, func_name, line_num)

    def _validate_docstring(self, docstring: str, func_name: str, line_num: int):
        """Validate docstring completeness for OpenAI SDK."""
        docstring_lower = docstring.lower()
        
        # Check for required sections
        missing_sections = []
        for section in self.REQUIRED_DOCSTRING_SECTIONS:
            if section not in docstring_lower:
                missing_sections.append(section)
        
        if missing_sections:
            self.issues.append({
                "type": "INCOMPLETE_DOCSTRING",
                "line": line_num,
                "function": func_name,
                "message": f"Missing docstring sections: {', '.join(missing_sections)}"
            })
        
        # Check for security considerations
        if 'security' not in docstring_lower and 'safe' not in docstring_lower:
            self.issues.append({
                "type": "MISSING_SECURITY_DOC",
                "line": line_num,
                "function": func_name,
                "message": "Tool docstring should document security considerations"
            })

    def _validate_type_hints(self, func: ast.FunctionDef, func_name: str, line_num: int):
        """Validate type hints for OpenAI SDK compatibility."""
        # Check return type annotation
        if not func.returns:
            self.issues.append({
                "type": "MISSING_RETURN_TYPE",
                "line": line_num,
                "function": func_name,
                "message": "Tool function missing return type annotation"
            })
        
        # Check parameter type annotations
        for arg in func.args.args:
            if not arg.annotation and arg.arg != 'self':
                self.issues.append({
                    "type": "MISSING_PARAM_TYPE",
                    "line": line_num,
                    "function": func_name,
                    "parameter": arg.arg,
                    "message": f"Parameter '{arg.arg}' missing type annotation"
                })

    def _validate_security_patterns(self, func: ast.FunctionDef, func_name: str, line_num: int):
        """Check for security anti-patterns."""
        
        class SecurityChecker(ast.NodeVisitor):
            def __init__(self, validator, func_name, base_line):
                self.validator = validator
                self.func_name = func_name
                self.base_line = base_line
                
            def visit_Call(self, node):
                """Check function calls for security issues."""
                func_call = self._get_call_name(node)
                
                # Check for dangerous operations
                for category, operations in self.validator.BLOCKED_OPERATIONS.items():
                    for op in operations:
                        if func_call and op in func_call:
                            self.validator.issues.append({
                                "type": "DANGEROUS_OPERATION",
                                "line": self.base_line + node.lineno - 1,
                                "function": self.func_name,
                                "category": category,
                                "message": f"Dangerous operation in tool: {func_call}"
                            })
                
                self.generic_visit(node)
                
            def visit_Str(self, node):
                """Check string literals for hardcoded secrets."""
                if len(node.s) > 20 and any(keyword in node.s.lower() 
                                          for keyword in ['key', 'token', 'password', 'secret']):
                    self.validator.issues.append({
                        "type": "POTENTIAL_HARDCODED_SECRET",
                        "line": self.base_line + node.lineno - 1,
                        "function": self.func_name,
                        "message": "Potential hardcoded secret in string literal"
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
        
        checker = SecurityChecker(self, func_name, line_num)
        checker.visit(func)

    def _validate_error_handling(self, func: ast.FunctionDef, func_name: str, line_num: int):
        """Check for proper error handling in tool functions."""
        
        class ErrorHandlingChecker(ast.NodeVisitor):
            def __init__(self, validator, func_name):
                self.validator = validator
                self.func_name = func_name
                self.has_try_except = False
                
            def visit_Try(self, node):
                self.has_try_except = True
                self.generic_visit(node)
        
        checker = ErrorHandlingChecker(self, func_name)
        checker.visit(func)
        
        # Tool functions should have error handling
        if not checker.has_try_except:
            self.issues.append({
                "type": "MISSING_ERROR_HANDLING",
                "line": line_num,
                "function": func_name,
                "message": "Tool function should include try/except error handling"
            })

    def _run_bandit_scan(self, file_path: Path):
        """Run Bandit security scanner on the file."""
        try:
            result = subprocess.run(
                ['bandit', '-f', 'json', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                bandit_data = json.loads(result.stdout)
                for issue in bandit_data.get('results', []):
                    self.issues.append({
                        "type": "BANDIT_SECURITY",
                        "line": issue.get('line_number', 0),
                        "severity": issue.get('issue_severity', 'UNKNOWN'),
                        "confidence": issue.get('issue_confidence', 'UNKNOWN'),
                        "message": f"Bandit: {issue.get('issue_text', 'Security issue')}"
                    })
                    
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, 
                json.JSONDecodeError, FileNotFoundError):
            # Bandit not available or failed - continue without it
            pass


def main():
    parser = argparse.ArgumentParser(description="Validate agent tool functions")
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args()
    
    validator = AgentToolValidator()
    exit_code = 0
    total_issues = 0
    
    for filename in args.filenames:
        file_path = Path(filename)
        
        # Only check Python files in agent directories
        if not (file_path.suffix == '.py' and 'agents' in file_path.parts):
            continue
            
        print(f"🛠️ Validating agent tools in {filename}...")
        
        issues = validator.validate_file(file_path)
        
        if issues:
            print(f"⚠️  Found {len(issues)} issues in {filename}:")
            for issue in issues:
                line_info = f":{issue.get('line', '?')}" if issue.get('line') else ""
                severity = issue.get('severity', 'HIGH')
                print(f"  ❌ {filename}{line_info} [{issue['type']}] [{severity}] {issue['message']}")
            
            total_issues += len(issues)
            
            # Critical issues fail the hook
            critical_types = ['DANGEROUS_OPERATION', 'MISSING_DOCSTRING', 'SYNTAX_ERROR']
            if any(issue['type'] in critical_types for issue in issues):
                exit_code = 1
    
    if total_issues == 0:
        print("✅ All agent tools validated successfully")
    else:
        print(f"\n🛠️ AGENT TOOL SUMMARY: Found {total_issues} total issues")
        if exit_code == 1:
            print("❌ Critical agent tool issues detected - commit blocked!")
            print("🔧 Please fix critical issues before committing.")
        else:
            print("⚠️  Non-critical issues detected - please review.")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())