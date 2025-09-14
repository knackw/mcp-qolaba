#!/usr/bin/env python3
"""
Code quality and linting runner for Qolaba MCP Server.

This script runs all configured linting tools including flake8, black, isort,
and ruff to ensure code quality and consistency across the project.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional


class LintingRunner:
    """Runs and manages code quality tools."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_paths = ["src", "tests", "scripts"]
        self.tools_config = {
            "black": {
                "command": ["black", "--check", "--diff"],
                "fix_command": ["black"],
                "description": "Code formatting with Black",
                "config_file": "pyproject.toml"
            },
            "isort": {
                "command": ["isort", "--check-only", "--diff"],
                "fix_command": ["isort"],
                "description": "Import sorting with isort",
                "config_file": "pyproject.toml"
            },
            "flake8": {
                "command": ["flake8"],
                "fix_command": None,  # flake8 doesn't auto-fix
                "description": "Code linting with flake8",
                "config_file": ".flake8"
            },
            "ruff": {
                "command": ["ruff", "check"],
                "fix_command": ["ruff", "check", "--fix"],
                "description": "Fast linting with ruff",
                "config_file": "pyproject.toml"
            },
            "mypy": {
                "command": ["mypy"],
                "fix_command": None,  # mypy doesn't auto-fix
                "description": "Static type checking with mypy",
                "config_file": "pyproject.toml"
            }
        }
    
    def check_tool_availability(self) -> Dict[str, bool]:
        """
        Check which linting tools are available.
        
        Returns:
            Dictionary mapping tool names to availability status
        """
        availability = {}
        
        for tool_name in self.tools_config.keys():
            try:
                result = subprocess.run(
                    [tool_name, "--version"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                availability[tool_name] = result.returncode == 0
            except FileNotFoundError:
                availability[tool_name] = False
        
        return availability
    
    def run_single_tool(self, tool_name: str, fix_mode: bool = False, 
                       paths: List[str] = None) -> Tuple[bool, str, str]:
        """
        Run a single linting tool.
        
        Args:
            tool_name: Name of the tool to run
            fix_mode: Whether to run in fix mode (auto-fix issues)
            paths: Specific paths to check (defaults to src_paths)
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if tool_name not in self.tools_config:
            return False, "", f"Unknown tool: {tool_name}"
        
        tool_config = self.tools_config[tool_name]
        
        if fix_mode and tool_config["fix_command"]:
            command = tool_config["fix_command"].copy()
        else:
            command = tool_config["command"].copy()
        
        # Add paths to command
        target_paths = paths or self.src_paths
        command.extend(target_paths)
        
        try:
            print(f"🔍 Running {tool_config['description']}...")
            print(f"   Command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            success = result.returncode == 0
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {tool_config['description']}: {'PASSED' if success else 'FAILED'}")
            
            if not success and result.stdout:
                print(f"   Output:\n{result.stdout}")
            if not success and result.stderr:
                print(f"   Errors:\n{result.stderr}")
            
            return success, result.stdout, result.stderr
            
        except FileNotFoundError:
            error_msg = f"{tool_name} not found. Please install it."
            print(f"❌ {error_msg}")
            return False, "", error_msg
    
    def run_all_tools(self, fix_mode: bool = False, 
                     skip_unavailable: bool = True) -> Tuple[bool, Dict[str, Tuple[bool, str, str]]]:
        """
        Run all configured linting tools.
        
        Args:
            fix_mode: Whether to run tools in fix mode
            skip_unavailable: Whether to skip unavailable tools
            
        Returns:
            Tuple of (overall_success, results_dict)
        """
        print("🚀 Starting code quality checks...")
        print("=" * 50)
        
        # Check tool availability
        availability = self.check_tool_availability()
        unavailable_tools = [tool for tool, available in availability.items() if not available]
        
        if unavailable_tools:
            print(f"⚠️  Unavailable tools: {', '.join(unavailable_tools)}")
            if not skip_unavailable:
                print("❌ Aborting due to unavailable tools. Install missing tools or use --skip-unavailable.")
                return False, {}
        
        results = {}
        overall_success = True
        
        # Run each available tool
        for tool_name, tool_config in self.tools_config.items():
            if availability.get(tool_name, False):
                success, stdout, stderr = self.run_single_tool(tool_name, fix_mode)
                results[tool_name] = (success, stdout, stderr)
                
                if not success:
                    overall_success = False
            else:
                print(f"⏭️  Skipping {tool_name} (not available)")
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 Summary:")
        
        for tool_name, (success, _, _) in results.items():
            status_icon = "✅" if success else "❌"
            print(f"   {status_icon} {self.tools_config[tool_name]['description']}")
        
        if overall_success:
            print("\n🎉 All code quality checks passed!")
        else:
            print("\n❌ Some code quality checks failed. Please fix the issues above.")
        
        return overall_success, results
    
    def format_code(self) -> bool:
        """
        Format code using black and isort.
        
        Returns:
            True if formatting completed successfully
        """
        print("🎨 Formatting code...")
        
        success = True
        
        # Run isort first (import sorting)
        if "isort" in self.check_tool_availability() and self.check_tool_availability()["isort"]:
            isort_success, _, _ = self.run_single_tool("isort", fix_mode=True)
            success = success and isort_success
        
        # Then run black (code formatting)
        if "black" in self.check_tool_availability() and self.check_tool_availability()["black"]:
            black_success, _, _ = self.run_single_tool("black", fix_mode=True)
            success = success and black_success
        
        return success
    
    def check_config_files(self) -> bool:
        """
        Check if all required configuration files exist.
        
        Returns:
            True if all config files exist
        """
        print("📋 Checking configuration files...")
        
        config_files = set()
        for tool_config in self.tools_config.values():
            if tool_config["config_file"]:
                config_files.add(tool_config["config_file"])
        
        missing_files = []
        for config_file in config_files:
            config_path = self.project_root / config_file
            if not config_path.exists():
                missing_files.append(config_file)
            else:
                print(f"✅ {config_file}")
        
        if missing_files:
            print(f"❌ Missing configuration files: {', '.join(missing_files)}")
            return False
        
        print("✅ All configuration files present")
        return True


def main():
    """Main entry point for linting runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run tools in fix mode (auto-fix issues where possible)"
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="Only run formatting tools (black, isort)"
    )
    parser.add_argument(
        "--tool",
        choices=["black", "isort", "flake8", "ruff"],
        help="Run only a specific tool"
    )
    parser.add_argument(
        "--skip-unavailable",
        action="store_true",
        default=True,
        help="Skip unavailable tools instead of failing"
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Only check if configuration files exist"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific paths to check (default: src, tests, scripts)"
    )
    
    args = parser.parse_args()
    
    runner = LintingRunner()
    
    # Check configuration files if requested
    if args.check_config:
        success = runner.check_config_files()
        sys.exit(0 if success else 1)
    
    # Format code only
    if args.format_only:
        success = runner.format_code()
        sys.exit(0 if success else 1)
    
    # Run single tool
    if args.tool:
        success, stdout, stderr = runner.run_single_tool(
            args.tool, 
            fix_mode=args.fix,
            paths=args.paths if args.paths else None
        )
        if not success:
            print(f"\nFull output:\n{stdout}")
            print(f"\nErrors:\n{stderr}")
        sys.exit(0 if success else 1)
    
    # Run all tools
    success, results = runner.run_all_tools(
        fix_mode=args.fix,
        skip_unavailable=args.skip_unavailable
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()