#!/usr/bin/env python3
"""
Script to run mypy on our qolaba_mcp_server code only.
"""

import subprocess
import sys
from pathlib import Path


def run_mypy_on_our_code():
    """Run mypy on our specific files to avoid fastmcp syntax issues."""

    # Find all Python files in our source directory
    src_dir = Path("src/qolaba_mcp_server")
    py_files = list(src_dir.rglob("*.py"))

    # Filter out __init__.py files and test files for now
    target_files = [
        str(f) for f in py_files
        if f.name != "__init__.py" and "test" not in str(f)
    ]

    if not target_files:
        print("No target files found")
        return 1

    print(f"Running mypy on {len(target_files)} files...")

    # Run mypy with basic configuration
    cmd = [
        "mypy",
        "--python-version", "3.10",
        "--ignore-missing-imports",
        "--no-strict-optional",
        "--show-error-codes",
        "--pretty"
    ] + target_files

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode
    except Exception as e:
        print(f"Error running mypy: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_mypy_on_our_code())