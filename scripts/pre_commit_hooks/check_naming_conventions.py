#!/usr/bin/env python3
"""
Naming Convention Check Hook
Enforces Orchestra AI coding standards for naming conventions.
"""

import ast
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any


class NamingConventionChecker:
    """Enforces naming conventions per Orchestra AI coding standards."""
    
    # Naming patterns
    PATTERNS = {
        'class': re.compile(r'^[A-Z][a-zA-Z0-9]*$'),           # PascalCase
        'function': re.compile(r'^[a-z][a-z0-9_]*$'),         # snake_case
        'method': re.compile(r'^[a-z][a-z0-9_]*$'),           # snake_case
        'variable': re.compile(r'^[a-z][a-z0-9_]*$'),         # snake_case
        'constant': re.compile(r'^[A-Z][A-Z0-9_]*$'),         # UPPER_SNAKE_CASE
        'private': re.compile(r'^_[a-z][a-z0-9_]*$'),         # _snake_case
        'module': re.compile(r'^[a-z][a-z0-9_]*$'),           # snake_case
    }
    
    # Special naming rules for AI agents
    AGENT_NAMING_RULES = {
        'agent_class': re.compile(r'^[A-Z][a-zA-Z0-9]*Agent$'),     # Must end with 'Agent'
        'tool_function': re.compile(r'^(get|set|create|update|delete|validate|process|analyze|generate)_[a-z0-9_]+$'),
        'workflow_function': re.compile(r'^[a-z][a-z0-9_]*_workflow$'),  # Must end with '_workflow'
    }
    
    # Reserved names that should not be used
    RESERVED_NAMES = {
        'openai', 'gpt', 'chatgpt', 'claude', 'anthropic',
        'system', 'user', 'assistant', 'prompt', 'completion'
    }

    def __init__(self):
        self.issues = []

    def check_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check naming conventions in a Python file."""
        self.issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (UnicodeDecodeError, SyntaxError) as e:
            return [{"type": "PARSE_ERROR", "message": f"Cannot parse {file_path}: {e}"}]
        
        # Check module name
        self._check_module_name(file_path)
        
        # Analyze AST for naming issues
        self._analyze_ast(tree, file_path)
        
        return self.issues

    def _check_module_name(self, file_path: Path):
        """Check if module name follows conventions."""
        module_name = file_path.stem
        
        # Skip special files
        if module_name in ['__init__', '__main__']:
            return
            
        if not self.PATTERNS['module'].match(module_name):
            self.issues.append({
                "type": "INVALID_MODULE_NAME",
                "line": 1,
                "name": module_name,
                "message": f"Module name '{module_name}' should be snake_case"
            })
        
        # Check for reserved names
        if module_name.lower() in self.RESERVED_NAMES:
            self.issues.append({
                "type": "RESERVED_NAME",
                "line": 1,
                "name": module_name,
                "severity": "HIGH",
                "message": f"Module name '{module_name}' is reserved"
            })

    def _analyze_ast(self, tree: ast.AST, file_path: Path):
        """Analyze AST for naming convention violations."""
        
        class NamingVisitor(ast.NodeVisitor):
            def __init__(self, checker, file_path):
                self.checker = checker
                self.file_path = file_path
                self.in_class = None
                
            def visit_ClassDef(self, node):
                """Check class naming."""
                old_class = self.in_class
                self.in_class = node.name
                
                self._check_class_name(node)
                self.generic_visit(node)
                
                self.in_class = old_class
                
            def visit_FunctionDef(self, node):
                """Check function naming."""
                self._check_function_name(node)
                self.generic_visit(node)
                
            def visit_AsyncFunctionDef(self, node):
                """Check async function naming."""
                self._check_function_name(node, is_async=True)
                self.generic_visit(node)
                
            def visit_Assign(self, node):
                """Check variable assignments."""
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self._check_variable_name(target, node.lineno)
                self.generic_visit(node)
                
            def _check_class_name(self, node: ast.ClassDef):
                """Validate class naming conventions."""
                class_name = node.name
                
                # Basic PascalCase check
                if not self.checker.PATTERNS['class'].match(class_name):
                    self.checker.issues.append({
                        "type": "INVALID_CLASS_NAME",
                        "line": node.lineno,
                        "name": class_name,
                        "message": f"Class '{class_name}' should be PascalCase"
                    })
                
                # Agent-specific naming
                if 'agents' in str(self.file_path):
                    if not self.checker.AGENT_NAMING_RULES['agent_class'].match(class_name):
                        self.checker.issues.append({
                            "type": "INVALID_AGENT_NAME",
                            "line": node.lineno,
                            "name": class_name,
                            "severity": "HIGH",
                            "message": f"Agent class '{class_name}' should end with 'Agent'"
                        })
                
                # Check for reserved names
                if class_name.lower() in self.checker.RESERVED_NAMES:
                    self.checker.issues.append({
                        "type": "RESERVED_CLASS_NAME",
                        "line": node.lineno,
                        "name": class_name,
                        "severity": "HIGH",
                        "message": f"Class name '{class_name}' is reserved"
                    })
                    
            def _check_function_name(self, node: ast.FunctionDef, is_async=False):
                """Validate function naming conventions."""
                func_name = node.name
                
                # Skip special methods
                if func_name.startswith('__') and func_name.endswith('__'):
                    return
                    
                # Check basic snake_case
                if func_name.startswith('_'):
                    pattern = self.checker.PATTERNS['private']
                else:
                    pattern = self.checker.PATTERNS['function']
                    
                if not pattern.match(func_name):
                    self.checker.issues.append({
                        "type": "INVALID_FUNCTION_NAME",
                        "line": node.lineno,
                        "name": func_name,
                        "message": f"Function '{func_name}' should be snake_case"
                    })
                
                # Agent-specific checks
                if 'agents' in str(self.file_path):
                    # Tool functions should follow tool naming pattern
                    if self._is_tool_function(node):
                        if not self.checker.AGENT_NAMING_RULES['tool_function'].match(func_name):
                            self.checker.issues.append({
                                "type": "INVALID_TOOL_NAME",
                                "line": node.lineno,
                                "name": func_name,
                                "severity": "HIGH",
                                "message": f"Tool function '{func_name}' should follow pattern: action_target"
                            })
                
                # Workflow-specific checks
                if 'workflows' in str(self.file_path):
                    if func_name.endswith('workflow') and not self.checker.AGENT_NAMING_RULES['workflow_function'].match(func_name):
                        self.checker.issues.append({
                            "type": "INVALID_WORKFLOW_NAME",
                            "line": node.lineno,
                            "name": func_name,
                            "severity": "HIGH",
                            "message": f"Workflow function '{func_name}' should end with '_workflow'"
                        })
                
                # Check for reserved names
                if func_name.lower() in self.checker.RESERVED_NAMES:
                    self.checker.issues.append({
                        "type": "RESERVED_FUNCTION_NAME",
                        "line": node.lineno,
                        "name": func_name,
                        "severity": "HIGH",
                        "message": f"Function name '{func_name}' is reserved"
                    })
                    
            def _check_variable_name(self, node: ast.Name, line_num: int):
                """Validate variable naming conventions."""
                var_name = node.id
                
                # Check if it's a constant (all uppercase)
                if var_name.isupper():
                    if not self.checker.PATTERNS['constant'].match(var_name):
                        self.checker.issues.append({
                            "type": "INVALID_CONSTANT_NAME",
                            "line": line_num,
                            "name": var_name,
                            "message": f"Constant '{var_name}' should be UPPER_SNAKE_CASE"
                        })
                else:
                    # Regular variable
                    if var_name.startswith('_'):
                        pattern = self.checker.PATTERNS['private']
                    else:
                        pattern = self.checker.PATTERNS['variable']
                        
                    if not pattern.match(var_name):
                        self.checker.issues.append({
                            "type": "INVALID_VARIABLE_NAME",
                            "line": line_num,
                            "name": var_name,
                            "message": f"Variable '{var_name}' should be snake_case"
                        })
                
                # Check for reserved names
                if var_name.lower() in self.checker.RESERVED_NAMES:
                    self.checker.issues.append({
                        "type": "RESERVED_VARIABLE_NAME",
                        "line": line_num,
                        "name": var_name,
                        "severity": "HIGH",
                        "message": f"Variable name '{var_name}' is reserved"
                    })
                    
            def _is_tool_function(self, node: ast.FunctionDef) -> bool:
                """Check if function is an agent tool."""
                # Check for tool decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id in ['tool', 'agent_tool']:
                            return True
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id in ['tool', 'agent_tool']:
                                return True
                return False
        
        visitor = NamingVisitor(self, file_path)
        visitor.visit(tree)


def main():
    parser = argparse.ArgumentParser(description="Check naming conventions")
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args()
    
    checker = NamingConventionChecker()
    exit_code = 0
    total_issues = 0
    
    for filename in args.filenames:
        file_path = Path(filename)
        
        # Only check Python files
        if file_path.suffix != '.py':
            continue
            
        print(f"📝 Checking naming conventions in {filename}...")
        
        issues = checker.check_file(file_path)
        
        if issues:
            print(f"⚠️  Found {len(issues)} naming issues in {filename}:")
            for issue in issues:
                line_info = f":{issue.get('line', '?')}" if issue.get('line') else ""
                severity = issue.get('severity', 'MEDIUM')
                print(f"  ❌ {filename}{line_info} [{issue['type']}] [{severity}] {issue['message']}")
            
            total_issues += len(issues)
            
            # High severity issues fail the hook
            if any(issue.get('severity') in ['CRITICAL', 'HIGH'] for issue in issues):
                exit_code = 1
    
    if total_issues == 0:
        print("✅ All naming conventions followed correctly")
    else:
        print(f"\n📝 NAMING SUMMARY: Found {total_issues} total issues")
        if exit_code == 1:
            print("❌ Critical naming issues detected - commit blocked!")
            print("🔧 Please fix naming convention issues before committing.")
        else:
            print("⚠️  Some naming improvements suggested - please review.")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())