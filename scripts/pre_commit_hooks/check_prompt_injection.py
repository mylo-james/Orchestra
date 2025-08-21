#!/usr/bin/env python3
"""
AI Prompt Injection Detection Hook
Prevents malicious prompt injection attempts in code and documentation.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


class PromptInjectionDetector:
    """Advanced prompt injection detection for AI safety."""
    
    # Comprehensive injection patterns
    INJECTION_PATTERNS = [
        # Direct instruction override
        r'ignore.*previous.*instructions',
        r'forget.*everything.*above',
        r'disregard.*all.*previous',
        r'you.*are.*now.*a?',
        r'system.*prompt.*is',
        r'new.*role.*you.*are',
        
        # Jailbreak attempts
        r'developer.*mode.*enabled',
        r'jailbreak.*activated',
        r'unrestricted.*mode',
        r'admin.*mode.*on',
        r'debug.*mode.*true',
        
        # Role manipulation
        r'act.*as.*if.*you.*are',
        r'pretend.*to.*be',
        r'roleplay.*as',
        r'simulate.*being',
        
        # Context manipulation
        r'in.*a.*hypothetical.*scenario',
        r'for.*educational.*purposes.*only',
        r'this.*is.*just.*a.*test',
        
        # Output manipulation
        r'output.*only',
        r'respond.*with.*only',
        r'answer.*must.*be',
        r'format.*your.*response',
        
        # System bypass
        r'\\n\\n.*system:',
        r'\\n\\n.*user:',
        r'\\n\\n.*assistant:',
        r'<\\|.*\\|>',
        
        # AI model specific
        r'gpt.*jailbreak',
        r'chatgpt.*hack',
        r'openai.*bypass',
        r'claude.*override',
    ]
    
    # Context-specific patterns for code files
    CODE_INJECTION_PATTERNS = [
        r'exec\(.*input\(',
        r'eval\(.*input\(',
        r'os\.system\(.*input\(',
        r'subprocess\..*shell=True',
        r'__import__\(.*input\(',
    ]
    
    # Suspicious prompt template patterns
    TEMPLATE_PATTERNS = [
        r'\{.*user_input.*\}.*system',
        r'f".*\{.*\}.*ignore',
        r'template.*\+.*user.*\+.*system',
    ]

    def __init__(self):
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                for pattern in self.INJECTION_PATTERNS]
        self.compiled_code_patterns = [re.compile(pattern, re.IGNORECASE) 
                                     for pattern in self.CODE_INJECTION_PATTERNS]
        self.compiled_template_patterns = [re.compile(pattern, re.IGNORECASE) 
                                         for pattern in self.TEMPLATE_PATTERNS]

    def scan_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Scan a file for prompt injection patterns."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            return issues
            
        for line_num, line in enumerate(lines, 1):
            # General injection patterns
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    issues.append((line_num, "PROMPT_INJECTION", 
                                 f"Potential prompt injection pattern: {pattern.pattern}"))
            
            # Code-specific patterns
            if file_path.suffix == '.py':
                for pattern in self.compiled_code_patterns:
                    if pattern.search(line):
                        issues.append((line_num, "CODE_INJECTION", 
                                     f"Dangerous code pattern: {pattern.pattern}"))
            
            # Template-specific patterns
            if any(keyword in line.lower() for keyword in ['template', 'prompt', 'format']):
                for pattern in self.compiled_template_patterns:
                    if pattern.search(line):
                        issues.append((line_num, "TEMPLATE_INJECTION", 
                                     f"Unsafe template pattern: {pattern.pattern}"))
        
        return issues

    def scan_content_blocks(self, file_path: Path) -> List[Tuple[str, str]]:
        """Scan for large content blocks that might contain hidden instructions."""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return issues
        
        # Check for suspiciously long strings or comments
        if file_path.suffix == '.py':
            # Multi-line strings
            multiline_strings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
            for string_content in multiline_strings:
                if len(string_content) > 1000:  # Suspiciously long
                    for pattern in self.compiled_patterns:
                        if pattern.search(string_content):
                            issues.append(("MULTILINE_STRING", 
                                         f"Injection in long string: {pattern.pattern}"))
        
        return issues


def main():
    parser = argparse.ArgumentParser(description="Check for prompt injection patterns")
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args()
    
    detector = PromptInjectionDetector()
    exit_code = 0
    
    for filename in args.filenames:
        file_path = Path(filename)
        
        # Skip non-text files
        if file_path.suffix in ['.pyc', '.pyo', '.so', '.dylib', '.exe']:
            continue
            
        print(f"🔍 Scanning {filename} for prompt injection patterns...")
        
        # Scan line by line
        line_issues = detector.scan_file(file_path)
        for line_num, issue_type, message in line_issues:
            print(f"❌ {filename}:{line_num} [{issue_type}] {message}")
            exit_code = 1
            
        # Scan content blocks
        content_issues = detector.scan_content_blocks(file_path)
        for issue_type, message in content_issues:
            print(f"❌ {filename} [{issue_type}] {message}")
            exit_code = 1
    
    if exit_code == 0:
        print("✅ No prompt injection patterns detected")
    else:
        print("\n🚨 SECURITY ALERT: Potential prompt injection patterns detected!")
        print("🛡️ Please review and remove any suspicious patterns before committing.")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())