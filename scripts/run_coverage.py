#!/usr/bin/env python3
"""
Test coverage runner and validator for Qolaba MCP Server.

This script runs tests with coverage reporting and validates that critical modules
meet the minimum coverage requirements specified in the project requirements.
"""

import subprocess
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple


class CoverageValidator:
    """Validates test coverage meets project requirements."""
    
    # Minimum coverage requirements as specified in project requirements
    MINIMUM_COVERAGE_REQUIREMENTS = {
        "src/qolaba_mcp_server/api/client.py": 80.0,           # API client module
        "src/qolaba_mcp_server/core/business_logic.py": 80.0,  # MCP handler/orchestrator
        "src/qolaba_mcp_server/models/api_models.py": 75.0,    # Data models
        "src/qolaba_mcp_server/config/settings.py": 70.0,     # Configuration
        "src/qolaba_mcp_server": 75.0  # Overall project minimum
    }
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.coverage_xml_file = self.project_root / "coverage.xml"
        self.coverage_html_dir = self.project_root / "htmlcov"
    
    def run_tests_with_coverage(self, test_paths: List[str] = None, verbose: bool = True) -> bool:
        """
        Run tests with coverage reporting.
        
        Args:
            test_paths: List of test paths to run. If None, runs all tests.
            verbose: Enable verbose output
            
        Returns:
            True if tests pass, False otherwise
        """
        print("🧪 Running tests with coverage reporting...")
        
        # Build pytest command with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=src/qolaba_mcp_server",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=term-missing",
            "--cov-branch"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if test_paths:
            cmd.extend(test_paths)
        else:
            cmd.extend(["tests/unit", "tests/integration"])
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=False)
            return result.returncode == 0
        except FileNotFoundError:
            print("❌ Error: pytest not found. Please install pytest and pytest-cov.")
            return False
    
    def parse_coverage_xml(self) -> Dict[str, float]:
        """
        Parse coverage.xml file to extract coverage percentages.
        
        Returns:
            Dictionary mapping file paths to coverage percentages
        """
        if not self.coverage_xml_file.exists():
            print(f"❌ Coverage XML file not found: {self.coverage_xml_file}")
            return {}
        
        try:
            tree = ET.parse(self.coverage_xml_file)
            root = tree.getroot()
            
            coverage_data = {}
            
            # Overall project coverage
            overall_coverage = float(root.attrib.get('line-rate', 0)) * 100
            coverage_data['src/qolaba_mcp_server'] = overall_coverage
            
            # Individual file coverage
            for package in root.findall('.//package'):
                package_name = package.attrib.get('name', '')
                
                for class_elem in package.findall('.//class'):
                    filename = class_elem.attrib.get('filename', '')
                    if filename:
                        line_rate = float(class_elem.attrib.get('line-rate', 0))
                        coverage_data[filename] = line_rate * 100
            
            return coverage_data
            
        except Exception as e:
            print(f"❌ Error parsing coverage XML: {e}")
            return {}
    
    def validate_coverage_requirements(self, coverage_data: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate that coverage meets minimum requirements.
        
        Args:
            coverage_data: Coverage data from XML parsing
            
        Returns:
            Tuple of (success, list of failure messages)
        """
        failures = []
        
        for file_path, required_coverage in self.MINIMUM_COVERAGE_REQUIREMENTS.items():
            actual_coverage = coverage_data.get(file_path)
            
            if actual_coverage is None:
                failures.append(f"❌ {file_path}: No coverage data found")
                continue
            
            if actual_coverage < required_coverage:
                failures.append(
                    f"❌ {file_path}: {actual_coverage:.1f}% coverage "
                    f"(required: {required_coverage:.1f}%)"
                )
            else:
                print(
                    f"✅ {file_path}: {actual_coverage:.1f}% coverage "
                    f"(required: {required_coverage:.1f}%)"
                )
        
        return len(failures) == 0, failures
    
    def generate_coverage_report(self) -> bool:
        """
        Generate comprehensive coverage report.
        
        Returns:
            True if coverage requirements are met, False otherwise
        """
        print("📊 Generating coverage report...")
        
        # Run tests with coverage
        if not self.run_tests_with_coverage():
            print("❌ Tests failed. Coverage validation aborted.")
            return False
        
        # Parse coverage data
        coverage_data = self.parse_coverage_xml()
        if not coverage_data:
            print("❌ Failed to parse coverage data.")
            return False
        
        # Display coverage summary
        print("\n📈 Coverage Summary:")
        print("=" * 60)
        
        for file_path, coverage in sorted(coverage_data.items()):
            status = "✅" if coverage >= self.MINIMUM_COVERAGE_REQUIREMENTS.get(file_path, 0) else "❌"
            print(f"{status} {file_path}: {coverage:.1f}%")
        
        # Validate requirements
        success, failures = self.validate_coverage_requirements(coverage_data)
        
        if success:
            print("\n🎉 All coverage requirements met!")
            print(f"📄 HTML report available at: {self.coverage_html_dir}/index.html")
            return True
        else:
            print("\n❌ Coverage requirements not met:")
            for failure in failures:
                print(f"  {failure}")
            return False
    
    def run_unit_tests_only(self) -> bool:
        """Run only unit tests with coverage."""
        print("🧪 Running unit tests only...")
        return self.run_tests_with_coverage(["tests/unit"])
    
    def run_integration_tests_only(self) -> bool:
        """Run only integration tests with coverage."""
        print("🧪 Running integration tests only...")
        return self.run_tests_with_coverage(["tests/integration"])


def main():
    """Main entry point for coverage validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests with coverage validation")
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip coverage validation"
    )
    
    args = parser.parse_args()
    
    validator = CoverageValidator()
    
    if args.unit_only:
        success = validator.run_unit_tests_only()
    elif args.integration_only:
        success = validator.run_integration_tests_only()
    else:
        success = validator.generate_coverage_report()
    
    if not success:
        sys.exit(1)
    
    print("\n✅ Coverage validation completed successfully!")


if __name__ == "__main__":
    main()