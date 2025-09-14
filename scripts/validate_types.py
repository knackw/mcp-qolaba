#!/usr/bin/env python3
"""
Type validation script for Qolaba MCP Server.

This script provides basic type checking and validation for our codebase
without requiring full mypy integration due to fastmcp compatibility issues.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class TypeChecker:
    """Basic type checking utility for our codebase."""

    def __init__(self):
        self.issues: List[Dict[str, str]] = []
        self.files_checked = 0
        self.functions_checked = 0

    def check_function_annotations(self, node: ast.FunctionDef, filename: str) -> None:
        """Check if function has type annotations."""
        # Skip special methods and private methods for now
        if node.name.startswith('__') and node.name.endswith('__'):
            return

        has_return_annotation = node.returns is not None
        missing_params = []

        for arg in node.args.args:
            if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':
                missing_params.append(arg.arg)

        if not has_return_annotation:
            self.issues.append({
                'file': filename,
                'line': node.lineno,
                'type': 'missing_return_annotation',
                'function': node.name,
                'message': f"Function '{node.name}' missing return type annotation"
            })

        if missing_params:
            self.issues.append({
                'file': filename,
                'line': node.lineno,
                'type': 'missing_param_annotations',
                'function': node.name,
                'message': f"Function '{node.name}' missing parameter annotations: {', '.join(missing_params)}"
            })

        self.functions_checked += 1

    def check_file(self, filepath: Path) -> None:
        """Check a single Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            self.files_checked += 1

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.check_function_annotations(node, str(filepath))

        except Exception as e:
            self.issues.append({
                'file': str(filepath),
                'line': 0,
                'type': 'parse_error',
                'function': '',
                'message': f"Error parsing file: {e}"
            })

    def check_directory(self, directory: Path) -> None:
        """Check all Python files in a directory."""
        for py_file in directory.rglob("*.py"):
            # Skip test files for now
            if "test" in str(py_file) or py_file.name.startswith("test_"):
                continue
            self.check_file(py_file)

    def report(self) -> None:
        """Generate and print the type checking report."""
        print(f"=== Type Checking Report ===")
        print(f"Files checked: {self.files_checked}")
        print(f"Functions checked: {self.functions_checked}")
        print(f"Issues found: {len(self.issues)}")
        print()

        if not self.issues:
            print("✅ No type annotation issues found!")
            return

        # Group issues by type
        by_type: Dict[str, List[Dict[str, str]]] = {}
        for issue in self.issues:
            issue_type = issue['type']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)

        for issue_type, issues in by_type.items():
            print(f"=== {issue_type.replace('_', ' ').title()} ({len(issues)} issues) ===")
            for issue in issues[:10]:  # Show first 10 of each type
                print(f"  {issue['file']}:{issue['line']} - {issue['message']}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")
            print()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path("src/qolaba_mcp_server")

    if not target_dir.exists():
        print(f"Error: Directory {target_dir} does not exist")
        return 1

    checker = TypeChecker()
    checker.check_directory(target_dir)
    checker.report()

    # Return non-zero if issues found
    return 1 if checker.issues else 0


if __name__ == "__main__":
    sys.exit(main())