#!/usr/bin/env python3
"""
Comprehensive test report generator for RiceGuard project.
Generates HTML reports, coverage analysis, and test metrics.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import xml.etree.ElementTree as ET


class TestReportGenerator:
    """Generates comprehensive test reports for the RiceGuard project."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.report_dir = project_root / "test-reports"
        self.report_dir.mkdir(exist_ok=True)

        # Component directories
        self.backend_dir = project_root / "src" / "backend"
        self.frontend_dir = project_root / "src" / "frontend"
        self.mobile_dir = project_root / "src" / "mobileapp" / "riceguard"

    def collect_test_results(self) -> Dict[str, Any]:
        """Collect test results from all components."""
        results = {
            "backend": self._collect_backend_results(),
            "frontend": self._collect_frontend_results(),
            "mobile": self._collect_mobile_results(),
            "timestamp": datetime.now().isoformat(),
        }

        return results

    def _collect_backend_results(self) -> Dict[str, Any]:
        """Collect backend test results."""
        backend_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "coverage": {},
            "security_tests": 0,
            "performance_tests": 0,
            "api_tests": 0,
            "integration_tests": 0,
            "unit_tests": 0,
        }

        try:
            # Run pytest with JSON output
            json_report_path = self.report_dir / "backend-results.json"
            cmd = [
                "python", "-m", "pytest",
                str(self.backend_dir / "tests"),
                "--json-report-file=" + str(json_report_path),
                "--json-report",
                "-v"
            ]

            result = subprocess.run(cmd, cwd=self.backend_dir, capture_output=True, text=True)

            if json_report_path.exists():
                with open(json_report_path, 'r') as f:
                    pytest_data = json.load(f)

                # Parse test results
                backend_results["total_tests"] = pytest_data.get("summary", {}).get("total", 0)
                backend_results["passed"] = pytest_data.get("summary", {}).get("passed", 0)
                backend_results["failed"] = pytest_data.get("summary", {}).get("failed", 0)
                backend_results["skipped"] = pytest_data.get("summary", {}).get("skipped", 0)

                # Categorize tests
                for test in pytest_data.get("tests", []):
                    outcome = test.get("outcome", "unknown")
                    keywords = test.get("keywords", [])

                    if "security" in keywords:
                        backend_results["security_tests"] += 1
                    if "performance" in keywords:
                        backend_results["performance_tests"] += 1
                    if "api" in keywords:
                        backend_results["api_tests"] += 1
                    if "integration" in keywords:
                        backend_results["integration_tests"] += 1
                    if "unit" in keywords:
                        backend_results["unit_tests"] += 1

            # Get coverage data
            coverage_xml = self.backend_dir / "coverage.xml"
            if coverage_xml.exists():
                backend_results["coverage"] = self._parse_coverage_xml(coverage_xml)

        except Exception as e:
            print(f"Error collecting backend results: {e}")

        return backend_results

    def _collect_frontend_results(self) -> Dict[str, Any]:
        """Collect frontend test results."""
        frontend_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "coverage": {},
            "component_tests": 0,
            "integration_tests": 0,
            "accessibility_tests": 0,
        }

        try:
            # Run Jest with JSON output
            json_report_path = self.report_dir / "frontend-results.json"
            cmd = [
                "npm", "test", "--",
                "--json", "--outputFile=" + str(json_report_path),
                "--passWithNoTests",
                "--watchAll=false"
            ]

            result = subprocess.run(cmd, cwd=self.frontend_dir, capture_output=True, text=True)

            if json_report_path.exists():
                with open(json_report_path, 'r') as f:
                    jest_data = json.load(f)

                # Parse Jest results
                frontend_results["total_tests"] = jest_data.get("numTotalTests", 0)
                frontend_results["passed"] = jest_data.get("numPassedTests", 0)
                frontend_results["failed"] = jest_data.get("numFailedTests", 0)
                frontend_results["skipped"] = jest_data.get("numPendingTests", 0)

                # Categorize tests
                for test_file in jest_data.get("testResults", []):
                    file_path = test_file.get("name", "")
                    if "component" in file_path.lower():
                        frontend_results["component_tests"] += 1
                    if "integration" in file_path.lower():
                        frontend_results["integration_tests"] += 1
                    if "accessibility" in file_path.lower():
                        frontend_results["accessibility_tests"] += 1

            # Get coverage data
            coverage_summary = self.frontend_dir / "coverage" / "coverage-summary.json"
            if coverage_summary.exists():
                with open(coverage_summary, 'r') as f:
                    coverage_data = json.load(f)

                frontend_results["coverage"] = {
                    "lines": coverage_data.get("total", {}).get("lines", {}).get("pct", 0),
                    "functions": coverage_data.get("total", {}).get("functions", {}).get("pct", 0),
                    "branches": coverage_data.get("total", {}).get("branches", {}).get("pct", 0),
                    "statements": coverage_data.get("total", {}).get("statements", {}).get("pct", 0),
                }

        except Exception as e:
            print(f"Error collecting frontend results: {e}")

        return frontend_results

    def _collect_mobile_results(self) -> Dict[str, Any]:
        """Collect mobile app test results."""
        mobile_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "coverage": {},
            "component_tests": 0,
            "screen_tests": 0,
            "integration_tests": 0,
            "accessibility_tests": 0,
        }

        try:
            # Run Jest with JSON output for mobile
            json_report_path = self.report_dir / "mobile-results.json"
            cmd = [
                "npm", "test", "--",
                "--json", "--outputFile=" + str(json_report_path),
                "--passWithNoTests",
                "--watchAll=false"
            ]

            result = subprocess.run(cmd, cwd=self.mobile_dir, capture_output=True, text=True)

            if json_report_path.exists():
                with open(json_report_path, 'r') as f:
                    jest_data = json.load(f)

                # Parse Jest results
                mobile_results["total_tests"] = jest_data.get("numTotalTests", 0)
                mobile_results["passed"] = jest_data.get("numPassedTests", 0)
                mobile_results["failed"] = jest_data.get("numFailedTests", 0)
                mobile_results["skipped"] = jest_data.get("numPendingTests", 0)

                # Categorize tests
                for test_file in jest_data.get("testResults", []):
                    file_path = test_file.get("name", "")
                    if "component" in file_path.lower():
                        mobile_results["component_tests"] += 1
                    if "screen" in file_path.lower():
                        mobile_results["screen_tests"] += 1
                    if "integration" in file_path.lower():
                        mobile_results["integration_tests"] += 1
                    if "accessibility" in file_path.lower():
                        mobile_results["accessibility_tests"] += 1

            # Get coverage data
            coverage_summary = self.mobile_dir / "coverage" / "coverage-summary.json"
            if coverage_summary.exists():
                with open(coverage_summary, 'r') as f:
                    coverage_data = json.load(f)

                mobile_results["coverage"] = {
                    "lines": coverage_data.get("total", {}).get("lines", {}).get("pct", 0),
                    "functions": coverage_data.get("total", {}).get("functions", {}).get("pct", 0),
                    "branches": coverage_data.get("total", {}).get("branches", {}).get("pct", 0),
                    "statements": coverage_data.get("total", {}).get("statements", {}).get("pct", 0),
                }

        except Exception as e:
            print(f"Error collecting mobile results: {e}")

        return mobile_results

    def _parse_coverage_xml(self, xml_path: Path) -> Dict[str, float]:
        """Parse coverage XML file."""
        coverage_data = {
            "lines": 0.0,
            "functions": 0.0,
            "branches": 0.0,
            "statements": 0.0,
        }

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for coverage in root.findall('.//coverage'):
                lines_valid = coverage.get('lines-valid', '0')
                lines_covered = coverage.get('lines-covered', '0')
                if lines_valid != '0':
                    coverage_data["lines"] = (int(lines_covered) / int(lines_valid)) * 100

                functions_valid = coverage.get('functions-valid', '0')
                functions_covered = coverage.get('functions-covered', '0')
                if functions_valid != '0':
                    coverage_data["functions"] = (int(functions_covered) / int(functions_valid)) * 100

                branches_valid = coverage.get('branches-valid', '0')
                branches_covered = coverage.get('branches-covered', '0')
                if branches_valid != '0':
                    coverage_data["branches"] = (int(branches_covered) / int(branches_valid)) * 100

                statements_valid = coverage.get('statements-valid', '0')
                statements_covered = coverage.get('statements-covered', '0')
                if statements_valid != '0':
                    coverage_data["statements"] = (int(statements_covered) / int(statements_valid)) * 100

        except Exception as e:
            print(f"Error parsing coverage XML: {e}")

        return coverage_data

    def calculate_overall_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall project metrics."""
        overall = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "success_rate": 0.0,
            "coverage": {
                "lines": 0.0,
                "functions": 0.0,
                "branches": 0.0,
                "statements": 0.0,
            },
            "component_breakdown": {
                "backend": results["backend"],
                "frontend": results["frontend"],
                "mobile": results["mobile"],
            }
        }

        # Sum test counts
        for component in ["backend", "frontend", "mobile"]:
            comp_results = results[component]
            overall["total_tests"] += comp_results.get("total_tests", 0)
            overall["passed"] += comp_results.get("passed", 0)
            overall["failed"] += comp_results.get("failed", 0)
            overall["skipped"] += comp_results.get("skipped", 0)

        # Calculate success rate
        if overall["total_tests"] > 0:
            overall["success_rate"] = (overall["passed"] / overall["total_tests"]) * 100

        # Calculate average coverage
        components_with_coverage = []
        for component in ["backend", "frontend", "mobile"]:
            comp_coverage = results[component].get("coverage", {})
            if comp_coverage:
                components_with_coverage.append(comp_coverage)

        if components_with_coverage:
            for metric in ["lines", "functions", "branches", "statements"]:
                values = [c[metric] for c in components_with_coverage if metric in c]
                if values:
                    overall["coverage"][metric] = sum(values) / len(values)

        return overall

    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML test report."""
        overall = self.calculate_overall_metrics(results)

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiceGuard Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }}
        .component-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .component-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
        }}
        .component-card h3 {{
            margin-top: 0;
            color: #007bff;
        }}
        .test-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }}
        .stat {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .stat-value {{
            font-weight: bold;
            font-size: 1.2em;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #666;
        }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .coverage-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .coverage-fill {{
            height: 100%;
            background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
            transition: width 0.3s ease;
        }}
        .success {{
            border-left-color: #28a745;
        }}
        .warning {{
            border-left-color: #ffc107;
        }}
        .error {{
            border-left-color: #dc3545;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RiceGuard Test Report</h1>
            <div class="timestamp">Generated: {results['timestamp']}</div>
        </div>

        <div class="metrics">
            <div class="metric-card {'success' if overall['success_rate'] >= 90 else 'warning' if overall['success_rate'] >= 70 else 'error'}">
                <div class="metric-value">{overall['success_rate']:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{overall['total_tests']}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric-card success">
                <div class="metric-value">{overall['passed']}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric-card error">
                <div class="metric-value">{overall['failed']}</div>
                <div class="metric-label">Failed</div>
            </div>
        </div>

        <div class="section">
            <h2>Overall Coverage</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Coverage</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>Lines</td>
                    <td>
                        <div class="coverage-bar">
                            <div class="coverage-fill" style="width: {overall['coverage']['lines']:.1f}%"></div>
                        </div>
                        {overall['coverage']['lines']:.1f}%
                    </td>
                    <td class="{'passed' if overall['coverage']['lines'] >= 80 else 'warning' if overall['coverage']['lines'] >= 60 else 'failed'}">
                        {'✅ Good' if overall['coverage']['lines'] >= 80 else '⚠️ Needs Work' if overall['coverage']['lines'] >= 60 else '❌ Poor'}
                    </td>
                </tr>
                <tr>
                    <td>Functions</td>
                    <td>
                        <div class="coverage-bar">
                            <div class="coverage-fill" style="width: {overall['coverage']['functions']:.1f}%"></div>
                        </div>
                        {overall['coverage']['functions']:.1f}%
                    </td>
                    <td class="{'passed' if overall['coverage']['functions'] >= 80 else 'warning' if overall['coverage']['functions'] >= 60 else 'failed'}">
                        {'✅ Good' if overall['coverage']['functions'] >= 80 else '⚠️ Needs Work' if overall['coverage']['functions'] >= 60 else '❌ Poor'}
                    </td>
                </tr>
                <tr>
                    <td>Branches</td>
                    <td>
                        <div class="coverage-bar">
                            <div class="coverage-fill" style="width: {overall['coverage']['branches']:.1f}%"></div>
                        </div>
                        {overall['coverage']['branches']:.1f}%
                    </td>
                    <td class="{'passed' if overall['coverage']['branches'] >= 80 else 'warning' if overall['coverage']['branches'] >= 60 else 'failed'}">
                        {'✅ Good' if overall['coverage']['branches'] >= 80 else '⚠️ Needs Work' if overall['coverage']['branches'] >= 60 else '❌ Poor'}
                    </td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Component Breakdown</h2>
            <div class="component-grid">
                {self._generate_component_html("Backend", results['backend'])}
                {self._generate_component_html("Frontend", results['frontend'])}
                {self._generate_component_html("Mobile", results['mobile'])}
            </div>
        </div>
    </div>
</body>
</html>
        """
        return html_template

    def _generate_component_html(self, name: str, component_data: Dict[str, Any]) -> str:
        """Generate HTML for a component card."""
        total_tests = component_data.get("total_tests", 0)
        passed = component_data.get("passed", 0)
        failed = component_data.get("failed", 0)
        skipped = component_data.get("skipped", 0)

        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        status_class = "success" if success_rate >= 90 else "warning" if success_rate >= 70 else "error"

        # Generate test category breakdown if available
        categories_html = ""
        if name == "Backend":
            categories = [
                ("Unit Tests", component_data.get("unit_tests", 0)),
                ("API Tests", component_data.get("api_tests", 0)),
                ("Security Tests", component_data.get("security_tests", 0)),
                ("Performance Tests", component_data.get("performance_tests", 0)),
            ]
        else:
            categories = [
                ("Component Tests", component_data.get("component_tests", 0)),
                ("Integration Tests", component_data.get("integration_tests", 0)),
                ("Accessibility Tests", component_data.get("accessibility_tests", 0)),
            ]
            if name == "Mobile":
                categories.insert(1, ("Screen Tests", component_data.get("screen_tests", 0)))

        categories_html = "<table><tr><th>Category</th><th>Count</th></tr>"
        for category, count in categories:
            categories_html += f"<tr><td>{category}</td><td>{count}</td></tr>"
        categories_html += "</table>"

        return f"""
        <div class="component-card {status_class}">
            <h3>{name}</h3>
            <div class="test-stats">
                <div class="stat">
                    <div class="stat-value passed">{passed}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat">
                    <div class="stat-value failed">{failed}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat">
                    <div class="stat-value skipped">{skipped}</div>
                    <div class="stat-label">Skipped</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{success_rate:.1f}%</div>
                    <div class="stat-label">Success</div>
                </div>
            </div>
            {categories_html}
        </div>
        """

    def generate_json_report(self, results: Dict[str, Any]) -> None:
        """Generate JSON report for machine consumption."""
        overall = self.calculate_overall_metrics(results)

        report_data = {
            "metadata": {
                "generated_at": results["timestamp"],
                "project": "RiceGuard",
                "version": "1.0.0",
            },
            "summary": overall,
            "components": results["component_breakdown"],
            "quality_gates": {
                "test_success_rate": overall["success_rate"] >= 90,
                "coverage_lines": overall["coverage"]["lines"] >= 80,
                "coverage_functions": overall["coverage"]["functions"] >= 80,
                "coverage_branches": overall["coverage"]["branches"] >= 80,
            },
        }

        json_path = self.report_dir / "test-report.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)

    def generate_badge_data(self, results: Dict[str, Any]) -> None:
        """Generate badge data for GitHub shields."""
        overall = self.calculate_overall_metrics(results)

        badge_data = {
            "schemaVersion": 1,
            "label": "tests",
            "message": f"{overall['passed']}/{overall['total_tests']} passed",
            "color": "brightgreen" if overall['success_rate'] >= 90 else "yellow" if overall['success_rate'] >= 70 else "red",
        }

        badge_path = self.report_dir / "test-badge.json"
        with open(badge_path, 'w') as f:
            json.dump(badge_data, f, indent=2)

    def generate_all_reports(self) -> None:
        """Generate all test reports."""
        print("🔍 Collecting test results...")
        results = self.collect_test_results()

        print("📊 Generating HTML report...")
        html_report = self.generate_html_report(results)
        html_path = self.report_dir / "index.html"
        with open(html_path, 'w') as f:
            f.write(html_report)

        print("📄 Generating JSON report...")
        self.generate_json_report(results)

        print("🏷️ Generating badge data...")
        self.generate_badge_data(results)

        # Generate summary
        overall = self.calculate_overall_metrics(results)
        print(f"\n📋 Test Summary:")
        print(f"   Total Tests: {overall['total_tests']}")
        print(f"   Passed: {overall['passed']}")
        print(f"   Failed: {overall['failed']}")
        print(f"   Success Rate: {overall['success_rate']:.1f}%")
        print(f"   Coverage Lines: {overall['coverage']['lines']:.1f}%")
        print(f"\n📁 Reports generated in: {self.report_dir}")
        print(f"   🌐 HTML Report: {html_path}")
        print(f"   📄 JSON Report: {self.report_dir / 'test-report.json'}")

        return overall


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate comprehensive test reports for RiceGuard")
    parser.add_argument("--project-root", type=str, help="Project root directory")

    args = parser.parse_args()

    if args.project_root:
        project_root = Path(args.project_root)
    else:
        # Default to script directory's parent
        project_root = Path(__file__).parent.parent

    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)

    try:
        generator = TestReportGenerator(project_root)
        overall = generator.generate_all_reports()

        # Exit with appropriate code based on results
        if overall['failed'] > 0 or overall['success_rate'] < 80:
            print(f"\n❌ Tests failed or success rate below 80%")
            sys.exit(1)
        else:
            print(f"\n✅ All tests passed successfully!")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()