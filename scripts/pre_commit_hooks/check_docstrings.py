#!/usr/bin/env python3
"""
Docstring Quality Check Hook
Ensures all functions and classes have proper docstrings for AI agent development.
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


class DocstringChecker:
    """Validates docstring quality and completeness."""
    
    # Required docstring sections for different function types
    AGENT_TOOL_SECTIONS = [
        'description', 'parameters', 'returns', 'raises', 'security'
    ]
    
    REGULAR_FUNCTION_SECTIONS = [
        'description', 'parameters', 'returns'
    ]
    
    CLASS_SECTIONS = [
        'description', 'attributes'
    ]

    def __init__(self):
        self.issues = []

    def check_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check docstrings in a Python file."""
        self.issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (UnicodeDecodeError, SyntaxError) as e:
            return [{"type": "PARSE_ERROR", "message": f"Cannot parse {file_path}: {e}"}]
        
        # Analyze all functions and classes
        self._analyze_node(tree, file_path)
        
        return self.issues

    def _analyze_node(self, tree: ast.AST, file_path: Path):
        """Analyze AST nodes for docstring issues."""
        
        class DocstringVisitor(ast.NodeVisitor):
            def __init__(self, checker, file_path):
                self.checker = checker
                self.file_path = file_path
                self.in_class = None
                
            def visit_ClassDef(self, node):
                """Check class docstrings."""
                old_class = self.in_class
                self.in_class = node.name
                
                self._check_class_docstring(node)
                self.generic_visit(node)
                
                self.in_class = old_class
                
            def visit_FunctionDef(self, node):
                """Check function docstrings."""
                self._check_function_docstring(node)
                self.generic_visit(node)
                
            def visit_AsyncFunctionDef(self, node):
                """Check async function docstrings."""
                self._check_function_docstring(node, is_async=True)
                self.generic_visit(node)
                
            def _check_class_docstring(self, node: ast.ClassDef):
                """Validate class docstring."""
                docstring = ast.get_docstring(node)
                
                if not docstring:
                    self.checker.issues.append({
                        "type": "MISSING_CLASS_DOCSTRING",
                        "line": node.lineno,
                        "name": node.name,
                        "message": f"Class {node.name} missing docstring"
                    })
                    return
                
                # Check docstring quality
                self._validate_docstring_sections(
                    docstring, node.name, node.lineno, 
                    self.checker.CLASS_SECTIONS, "class"
                )
                
            def _check_function_docstring(self, node: ast.FunctionDef, is_async=False):
                """Validate function docstring."""
                func_name = node.name
                
                # Skip private methods and special methods
                if func_name.startswith('_'):
                    return
                    
                docstring = ast.get_docstring(node)
                
                if not docstring:
                    severity = self._get_docstring_severity(node, self.file_path)
                    self.checker.issues.append({
                        "type": "MISSING_FUNCTION_DOCSTRING",
                        "line": node.lineno,
                        "name": func_name,
                        "severity": severity,
                        "message": f"Function {func_name} missing docstring"
                    })
                    return
                
                # Determine required sections based on function type
                is_agent_tool = self._is_agent_tool_function(node)
                required_sections = (self.checker.AGENT_TOOL_SECTIONS if is_agent_tool 
                                   else self.checker.REGULAR_FUNCTION_SECTIONS)
                
                self._validate_docstring_sections(
                    docstring, func_name, node.lineno, 
                    required_sections, "agent_tool" if is_agent_tool else "function"
                )
                
            def _is_agent_tool_function(self, node: ast.FunctionDef) -> bool:
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
                
                # Check if in agent directory
                return 'agents' in str(self.file_path)
                
            def _get_docstring_severity(self, node: ast.FunctionDef, file_path: Path) -> str:
                """Get severity for missing docstring."""
                # Agent tools are critical
                if self._is_agent_tool_function(node):
                    return "CRITICAL"
                    
                # Security functions are critical
                if 'security' in str(file_path):
                    return "CRITICAL"
                    
                # Public functions in core modules
                if any(part in str(file_path) for part in ['workflows', 'services']):
                    return "HIGH"
                    
                return "MEDIUM"
                
            def _validate_docstring_sections(self, docstring: str, name: str, 
                                           line: int, required_sections: List[str], 
                                           func_type: str):
                """Validate docstring sections."""
                docstring_lower = docstring.lower()
                missing_sections = []
                
                for section in required_sections:
                    # Flexible section matching
                    section_patterns = {
                        'description': ['description', 'summary'],
                        'parameters': ['parameters', 'params', 'args', 'arguments'],
                        'returns': ['returns', 'return'],
                        'raises': ['raises', 'raise', 'exceptions'],
                        'security': ['security', 'safety', 'validation'],
                        'attributes': ['attributes', 'attrs']
                    }
                    
                    patterns = section_patterns.get(section, [section])
                    if not any(pattern in docstring_lower for pattern in patterns):
                        missing_sections.append(section)
                
                if missing_sections:
                    severity = "CRITICAL" if func_type == "agent_tool" else "HIGH"
                    self.checker.issues.append({
                        "type": "INCOMPLETE_DOCSTRING",
                        "line": line,
                        "name": name,
                        "severity": severity,
                        "missing_sections": missing_sections,
                        "message": f"{func_type.title()} {name} missing docstring sections: {', '.join(missing_sections)}"
                    })
        
        visitor = DocstringVisitor(self, file_path)
        visitor.visit(tree)


def main():
    parser = argparse.ArgumentParser(description="Check docstring quality")
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args()
    
    checker = DocstringChecker()
    exit_code = 0
    total_issues = 0
    
    for filename in args.filenames:
        file_path = Path(filename)
        
        # Only check Python files
        if file_path.suffix != '.py':
            continue
            
        print(f"📚 Checking docstrings in {filename}...")
        
        issues = checker.check_file(file_path)
        
        if issues:
            print(f"⚠️  Found {len(issues)} docstring issues in {filename}:")
            for issue in issues:
                line_info = f":{issue.get('line', '?')}" if issue.get('line') else ""
                severity = issue.get('severity', 'MEDIUM')
                print(f"  ❌ {filename}{line_info} [{issue['type']}] [{severity}] {issue['message']}")
                
                if 'missing_sections' in issue:
                    print(f"     Missing: {', '.join(issue['missing_sections'])}")
            
            total_issues += len(issues)
            
            # Critical issues fail the hook
            if any(issue.get('severity') == 'CRITICAL' for issue in issues):
                exit_code = 1
    
    if total_issues == 0:
        print("✅ All docstrings are properly documented")
    else:
        print(f"\n📚 DOCSTRING SUMMARY: Found {total_issues} total issues")
        if exit_code == 1:
            print("❌ Critical docstring issues detected - commit blocked!")
            print("📝 Please add proper docstrings for agent tools and security functions.")
        else:
            print("⚠️  Some docstring improvements needed - please review.")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())