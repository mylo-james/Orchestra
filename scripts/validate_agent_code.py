#!/usr/bin/env python3
"""
Agent Code Validation Script
Validates agent code files for OpenAI SDK compliance and security.
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any


class AgentCodeValidator:
    """Validates agent code for compliance and security."""
    
    def __init__(self):
        self.issues = []

    def validate_agent_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate a single agent file."""
        self.issues = []
        
        print(f"🤖 Validating agent file: {file_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (UnicodeDecodeError, SyntaxError) as e:
            return [{"type": "PARSE_ERROR", "message": f"Cannot parse {file_path}: {e}"}]
        
        # 1. Check for required imports
        self._check_required_imports(tree)
        
        # 2. Validate agent class structure
        self._validate_agent_classes(tree)
        
        # 3. Check tool functions
        self._validate_tool_functions(tree)
        
        # 4. Security validation
        self._validate_security_compliance(tree)
        
        return self.issues

    def _check_required_imports(self, tree: ast.AST):
        """Check for required imports in agent files."""
        imports = set()
        
        class ImportCollector(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    imports.add(alias.name)
                    
            def visit_ImportFrom(self, node):
                if node.module:
                    imports.add(node.module)
        
        collector = ImportCollector()
        collector.visit(tree)
        
        # Required imports for agent files
        required_imports = ['openai', 'pydantic', 'typing']
        
        for required in required_imports:
            if not any(required in imp for imp in imports):
                self.issues.append({
                    "type": "MISSING_REQUIRED_IMPORT",
                    "severity": "HIGH",
                    "import": required,
                    "message": f"Agent file missing required import: {required}"
                })

    def _validate_agent_classes(self, tree: ast.AST):
        """Validate agent class structure."""
        
        class AgentClassFinder(ast.NodeVisitor):
            def __init__(self, validator):
                self.validator = validator
                self.found_agent_class = False
                
            def visit_ClassDef(self, node):
                class_name = node.name
                
                # Check if this is an agent class
                if class_name.endswith('Agent'):
                    self.found_agent_class = True
                    self._validate_agent_class(node)
                    
                self.generic_visit(node)
                
            def _validate_agent_class(self, node: ast.ClassDef):
                """Validate individual agent class."""
                class_name = node.name
                
                # Check for required methods
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                
                required_methods = ['__init__']
                for method in required_methods:
                    if method not in methods:
                        self.validator.issues.append({
                            "type": "MISSING_AGENT_METHOD",
                            "line": node.lineno,
                            "class": class_name,
                            "method": method,
                            "severity": "HIGH",
                            "message": f"Agent class {class_name} missing required method: {method}"
                        })
                
                # Check for proper inheritance
                if not node.bases:
                    self.validator.issues.append({
                        "type": "MISSING_AGENT_BASE_CLASS",
                        "line": node.lineno,
                        "class": class_name,
                        "severity": "MEDIUM",
                        "message": f"Agent class {class_name} should inherit from base agent class"
                    })
        
        finder = AgentClassFinder(self)
        finder.visit(tree)
        
        if not finder.found_agent_class:
            self.issues.append({
                "type": "NO_AGENT_CLASS_FOUND",
                "severity": "HIGH",
                "message": "No agent class found in agent file"
            })

    def _validate_tool_functions(self, tree: ast.AST):
        """Validate agent tool functions."""
        
        class ToolFunctionValidator(ast.NodeVisitor):
            def __init__(self, validator):
                self.validator = validator
                
            def visit_FunctionDef(self, node):
                if self._is_tool_function(node):
                    self._validate_tool_function(node)
                self.generic_visit(node)
                
            def _is_tool_function(self, node: ast.FunctionDef) -> bool:
                """Check if function is a tool function."""
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
                
            def _validate_tool_function(self, node: ast.FunctionDef):
                """Validate tool function compliance."""
                func_name = node.name
                
                # 1. Check docstring
                docstring = ast.get_docstring(node)
                if not docstring:
                    self.validator.issues.append({
                        "type": "TOOL_MISSING_DOCSTRING",
                        "line": node.lineno,
                        "function": func_name,
                        "severity": "CRITICAL",
                        "message": f"Tool function {func_name} missing docstring"
                    })
                
                # 2. Check type annotations
                if not node.returns:
                    self.validator.issues.append({
                        "type": "TOOL_MISSING_RETURN_TYPE",
                        "line": node.lineno,
                        "function": func_name,
                        "severity": "HIGH",
                        "message": f"Tool function {func_name} missing return type annotation"
                    })
                
                # 3. Check for error handling
                has_try_except = any(isinstance(n, ast.Try) for n in ast.walk(node))
                if not has_try_except:
                    self.validator.issues.append({
                        "type": "TOOL_MISSING_ERROR_HANDLING",
                        "line": node.lineno,
                        "function": func_name,
                        "severity": "HIGH",
                        "message": f"Tool function {func_name} missing error handling"
                    })
        
        validator = ToolFunctionValidator(self)
        validator.visit(tree)

    def _validate_security_compliance(self, tree: ast.AST):
        """Validate security compliance of agent code."""
        
        class SecurityValidator(ast.NodeVisitor):
            def __init__(self, validator):
                self.validator = validator
                
            def visit_Call(self, node):
                """Check function calls for security issues."""
                func_name = self._get_call_name(node)
                
                # Dangerous function calls
                dangerous_calls = [
                    'eval', 'exec', 'os.system', 'subprocess.run',
                    '__import__', 'compile', 'open'
                ]
                
                if func_name in dangerous_calls:
                    self.validator.issues.append({
                        "type": "DANGEROUS_FUNCTION_CALL",
                        "line": node.lineno,
                        "function": func_name,
                        "severity": "CRITICAL",
                        "message": f"Dangerous function call in agent: {func_name}"
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
        
        validator = SecurityValidator(self)
        validator.visit(tree)


def main():
    parser = argparse.ArgumentParser(description="Validate agent code files")
    parser.add_argument('files', nargs='+', help='Agent files to validate')
    args = parser.parse_args()
    
    validator = AgentCodeValidator()
    exit_code = 0
    total_issues = 0
    
    for filename in args.files:
        file_path = Path(filename)
        
        if not file_path.exists():
            print(f"❌ File not found: {filename}")
            exit_code = 1
            continue
            
        if file_path.suffix != '.py':
            print(f"⚠️  Skipping non-Python file: {filename}")
            continue
        
        issues = validator.validate_agent_file(file_path)
        
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
        print(f"\n✅ All {len(args.files)} agent files validated successfully")
    else:
        print(f"\n🤖 AGENT VALIDATION SUMMARY: Found {total_issues} total issues")
        if exit_code == 1:
            print("❌ Critical agent validation issues detected!")
            print("🔧 Please fix issues before proceeding.")
        else:
            print("⚠️  Some improvements suggested - please review.")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())