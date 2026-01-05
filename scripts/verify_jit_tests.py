#!/usr/bin/env python3
"""
Verification script to ensure all JIT functions have corresponding test files.

This script:
1. Finds all functions decorated with @njit or @jit
2. Checks if they have # pragma: no cover
3. Verifies test file references in docstrings
4. Checks if test files exist and test the functions

Usage:
    python scripts/verify_jit_tests.py
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys


class JITFunctionVisitor(ast.NodeVisitor):
    """AST visitor to find JIT-decorated functions."""
    
    def __init__(self):
        self.jit_functions: List[Dict] = []
        self.current_file: Optional[Path] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions to find JIT decorators."""
        # Check for @njit or @jit decorators
        has_jit = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id in ('njit', 'jit'):
                        has_jit = True
                        break
            elif isinstance(decorator, ast.Name):
                if decorator.id in ('njit', 'jit'):
                    has_jit = True
                    break
        
        if has_jit:
            # Get function signature
            func_name = node.name
            line_no = node.lineno
            
            # Read source to check for pragma and docstring
            if self.current_file:
                try:
                    source_lines = self.current_file.read_text(encoding='utf-8').split('\n')
                except UnicodeDecodeError:
                    # Skip if encoding error
                    return
                func_start = line_no - 1
                
                # Check for # pragma: no cover
                has_pragma = False
                for i in range(func_start, min(func_start + 5, len(source_lines))):
                    if '# pragma: no cover' in source_lines[i]:
                        has_pragma = True
                        break
                
                # Get docstring
                docstring = ast.get_docstring(node)
                
                # Check for test file reference in docstring
                test_file_ref = None
                if docstring:
                    # Look for patterns like "tested in tests/test_*.py"
                    test_pattern = r'test[s]?[ed]?\s+in\s+([\w/\.]+\.py)'
                    match = re.search(test_pattern, docstring, re.IGNORECASE)
                    if match:
                        test_file_ref = match.group(1)
                
                self.jit_functions.append({
                    'file': str(self.current_file),
                    'function': func_name,
                    'line': line_no,
                    'has_pragma': has_pragma,
                    'has_docstring': docstring is not None,
                    'test_file_ref': test_file_ref,
                    'docstring': docstring,
                })
        
        self.generic_visit(node)


def find_jit_functions(root_dir: Path) -> List[Dict]:
    """Find all JIT functions in the codebase."""
    visitor = JITFunctionVisitor()
    
    # Find all Python files in smrforge directory
    for py_file in root_dir.rglob('*.py'):
        # Skip test files and __pycache__
        if 'test' in py_file.name.lower() or '__pycache__' in str(py_file):
            continue
        
        # Skip if not in smrforge package
        if 'smrforge' not in str(py_file):
            continue
        
        try:
            visitor.current_file = py_file
            # Read with UTF-8 encoding, skip files with encoding errors
            try:
                content = py_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Skip files with encoding issues
                continue
            tree = ast.parse(content)
            visitor.visit(tree)
        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors or encoding issues
            continue
    
    return visitor.jit_functions


def check_test_files(jit_functions: List[Dict], tests_dir: Path) -> Dict[str, bool]:
    """Check if test files exist and test the JIT functions."""
    results = {}
    
    for func_info in jit_functions:
        func_name = func_info['function']
        test_file_ref = func_info['test_file_ref']
        
        # Try to find test file
        test_file_found = False
        
        if test_file_ref:
            # Check if referenced test file exists
            test_file_path = tests_dir / test_file_ref
            if test_file_path.exists():
                # Check if function is tested in that file
                try:
                    test_content = test_file_path.read_text(encoding='utf-8')
                    # Look for function name in test file
                    if func_name in test_content or func_name.replace('_', '') in test_content:
                        test_file_found = True
                except UnicodeDecodeError:
                    # Skip files with encoding issues
                    pass
        
        # Also search for function name in test files
        if not test_file_found:
            for test_file in tests_dir.rglob('test_*.py'):
                try:
                    test_content = test_file.read_text(encoding='utf-8')
                    if func_name in test_content:
                        test_file_found = True
                        break
                except UnicodeDecodeError:
                    # Skip files with encoding issues
                    continue
        
        results[func_name] = test_file_found
    
    return results


def main():
    """Main verification function."""
    root_dir = Path(__file__).parent.parent
    smrforge_dir = root_dir / 'smrforge'
    tests_dir = root_dir / 'tests'
    
    if not smrforge_dir.exists():
        print(f"Error: smrforge directory not found at {smrforge_dir}")
        sys.exit(1)
    
    print("Finding JIT functions...")
    jit_functions = find_jit_functions(smrforge_dir)
    
    if not jit_functions:
        print("OK: No JIT functions found (or all in test files)")
        return 0
    
    print(f"\nFound {len(jit_functions)} JIT function(s):\n")
    
    # Check test files
    test_results = check_test_files(jit_functions, tests_dir)
    
    # Report results
    all_good = True
    issues = []
    
    for func_info in jit_functions:
        func_name = func_info['function']
        file_path = func_info['file']
        line_no = func_info['line']
        
        status = []
        
        # Check pragma
        if not func_info['has_pragma']:
            status.append("[X] Missing # pragma: no cover")
            all_good = False
            issues.append(f"{func_name} ({file_path}:{line_no}) - Missing # pragma: no cover")
        else:
            status.append("[OK] Has # pragma: no cover")
        
        # Check docstring
        if not func_info['has_docstring']:
            status.append("[!] Missing docstring")
            issues.append(f"{func_name} ({file_path}:{line_no}) - Missing docstring")
        else:
            status.append("[OK] Has docstring")
        
        # Check test file reference
        if not func_info['test_file_ref']:
            status.append("[!] No test file reference in docstring")
            issues.append(f"{func_name} ({file_path}:{line_no}) - No test file reference in docstring")
        else:
            status.append(f"[OK] References test file: {func_info['test_file_ref']}")
        
        # Check if test file exists
        if not test_results.get(func_name, False):
            status.append("[X] Test file not found or function not tested")
            all_good = False
            issues.append(f"{func_name} ({file_path}:{line_no}) - Test file not found or function not tested")
        else:
            status.append("[OK] Test file found")
        
        print(f"  {func_name} ({Path(file_path).relative_to(root_dir)}:{line_no})")
        for s in status:
            print(f"    {s}")
        print()
    
    # Summary
    print("=" * 70)
    if all_good and not issues:
        print("[OK] All JIT functions are properly documented and tested!")
        return 0
    else:
        print(f"[!] Found {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  - {issue}")
        print("\nSee docs/development/jit_function_test_registry.md for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

