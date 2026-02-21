#!/usr/bin/env python3
"""
Test Quality Validation Tools and Commands

Implements quality validation, analysis, and reporting tools
for the MCP Gateway test creation workflows.

Quality Over Quantity: Every validation focuses on real confidence and value.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import re
import ast


@dataclass
class QualityMetrics:
    """Comprehensive test quality metrics."""
    business_logic_coverage: float
    error_scenario_coverage: float
    mock_isolation_score: float
    realistic_data_score: float
    test_complexity_score: float
    documentation_quality: float
    maintenance_score: float
    overall_quality_score: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class TestQualityIssue:
    """Represents a quality issue found in tests."""
    severity: str  # critical, high, medium, low
    category: str  # false_positive, missing_coverage, poor_isolation, etc.
    description: str
    file_path: str
    line_number: Optional[int]
    suggestion: str


class TestQualityAnalyzer:
    """Analyzes test files for quality issues and metrics."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tool_router_path = project_root / "tool_router"

        # Quality patterns and anti-patterns
        self.false_positive_patterns = [
            r"def test_.*_enum.*\(\):",
            r"assert\s+\w+\s*==\s*\w+\s*$",  # Simple enum/value tests
            r"assert\s+len\(\w+\)\s*==\s*\d+\s*$",  # Simple length tests
            r"assert\s+isinstance\(\w+,\s*\w+\)\s*$",  # Simple type tests
        ]

        self.quality_indicators = [
            r"def test_.*_business_logic",
            r"def test_.*_error",
            r"def test_.*_integration",
            r"@patch\(",
            r"MagicMock\(",
            r"AsyncMock\(",
            r"pytest\.raises\(",
        ]

    def analyze_test_file(self, test_file: Path) -> Tuple[QualityMetrics, List[TestQualityIssue]]:
        """Analyze a single test file for quality metrics and issues."""
        print(f"🔍 Analyzing test file: {test_file}")

        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0), [
                TestQualityIssue("critical", "file_error", f"Could not read file: {e}", str(test_file), None, "Fix file permissions or encoding")
            ]

        issues = []

        # Check for false positive patterns
        false_positive_issues = self._check_false_positive_patterns(content, test_file)
        issues.extend(false_positive_issues)

        # Calculate quality metrics
        metrics = self._calculate_quality_metrics(content, test_file)

        # Check for specific quality issues
        missing_coverage_issues = self._check_missing_coverage(content, test_file)
        issues.extend(missing_coverage_issues)

        isolation_issues = self._check_test_isolation(content, test_file)
        issues.extend(isolation_issues)

        documentation_issues = self._check_documentation(content, test_file)
        issues.extend(documentation_issues)

        return metrics, issues

    def _check_false_positive_patterns(self, content: str, test_file: Path) -> List[TestQualityIssue]:
        """Check for false positive test patterns."""
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.false_positive_patterns:
                if re.search(pattern, line.strip()):
                    issues.append(TestQualityIssue(
                        severity="medium",
                        category="false_positive",
                        description=f"Potential false positive test pattern detected",
                        file_path=str(test_file),
                        line_number=i,
                        suggestion="Replace with meaningful business logic test or remove if not valuable"
                    ))

        return issues

    def _check_missing_coverage(self, content: str, test_file: Path) -> List[TestQualityIssue]:
        """Check for missing test coverage types."""
        issues = []

        # Check for missing error scenario tests
        if "pytest.raises" not in content and "except" not in content:
            issues.append(TestQualityIssue(
                severity="medium",
                category="missing_coverage",
                description="No error scenario tests found",
                file_path=str(test_file),
                line_number=None,
                suggestion="Add tests for error conditions and edge cases"
            ))

        # Check for missing business logic tests
        if not any(indicator in content for indicator in ["if", "for", "while", "try"]):
            issues.append(TestQualityIssue(
                severity="high",
                category="missing_coverage",
                description="No business logic tests found",
                file_path=str(test_file),
                line_number=None,
                suggestion="Add tests that verify actual business logic and decision paths"
            ))

        return issues

    def _check_test_isolation(self, content: str, test_file: Path) -> List[TestQualityIssue]:
        """Check for proper test isolation and mocking."""
        issues = []

        # Check for external dependencies without mocking
        external_patterns = ["requests.", "httpx.", "open(", "os.path", "sqlite3."]
        has_external = any(pattern in content for pattern in external_patterns)
        has_mocks = any(mock in content for mock in ["@patch", "MagicMock", "mock_open"])

        if has_external and not has_mocks:
            issues.append(TestQualityIssue(
                severity="high",
                category="poor_isolation",
                description="External dependencies found without proper mocking",
                file_path=str(test_file),
                line_number=None,
                suggestion="Add appropriate mocks for external dependencies"
            ))

        return issues

    def _check_documentation(self, content: str, test_file: Path) -> List[TestQualityIssue]:
        """Check for proper test documentation."""
        issues = []

        # Count test functions with docstrings
        test_functions = re.findall(r"def test_.*?\):", content)
        docstring_tests = re.findall(r"def test_.*?\):\s*\"\"\"", content)

        if len(test_functions) > 0 and len(docstring_tests) / len(test_functions) < 0.5:
            issues.append(TestQualityIssue(
                severity="low",
                category="poor_documentation",
                description="Many test functions lack docstrings",
                file_path=str(test_file),
                line_number=None,
                suggestion="Add descriptive docstrings to test functions"
            ))

        return issues

    def _calculate_quality_metrics(self, content: str, test_file: Path) -> QualityMetrics:
        """Calculate comprehensive quality metrics for a test file."""

        # Business Logic Coverage (30% weight)
        business_indicators = ["if", "for", "while", "try", "except", "with"]
        business_score = sum(1 for indicator in business_indicators if indicator in content)
        business_logic_coverage = min(100, business_score * 10)

        # Error Scenario Coverage (25% weight)
        error_indicators = ["pytest.raises", "except", "raise", "assert False"]
        error_score = sum(1 for indicator in error_indicators if indicator in content)
        error_scenario_coverage = min(100, error_score * 15)

        # Mock Isolation Score (20% weight)
        mock_indicators = ["@patch", "MagicMock", "AsyncMock", "mock_open"]
        mock_score = sum(1 for indicator in mock_indicators if indicator in content)
        mock_isolation_score = min(100, mock_score * 20)

        # Realistic Data Score (15% weight)
        data_indicators = ["fixture", "realistic", "sample_data", "test_data"]
        data_score = sum(1 for indicator in data_indicators if indicator in content.lower())
        realistic_data_score = min(100, data_score * 25)

        # Test Complexity Score (5% weight)
        test_functions = len(re.findall(r"def test_", content))
        complexity_score = min(100, test_functions * 5)

        # Documentation Quality (5% weight)
        docstring_ratio = 0
        test_functions_with_docs = len(re.findall(r"def test_.*?\):\s*\"\"\"", content))
        total_test_functions = len(re.findall(r"def test_", content))
        if total_test_functions > 0:
            docstring_ratio = (test_functions_with_docs / total_test_functions) * 100
        documentation_quality = docstring_ratio

        # Maintenance Score (calculated from other metrics)
        maintenance_score = (
            business_logic_coverage * 0.3 +
            mock_isolation_score * 0.4 +
            documentation_quality * 0.3
        )

        # Overall Quality Score
        overall_quality_score = (
            business_logic_coverage * 0.30 +
            error_scenario_coverage * 0.25 +
            mock_isolation_score * 0.20 +
            realistic_data_score * 0.15 +
            complexity_score * 0.05 +
            documentation_quality * 0.05
        )

        return QualityMetrics(
            business_logic_coverage=business_logic_coverage,
            error_scenario_coverage=error_scenario_coverage,
            mock_isolation_score=mock_isolation_score,
            realistic_data_score=realistic_data_score,
            test_complexity_score=complexity_score,
            documentation_quality=documentation_quality,
            maintenance_score=maintenance_score,
            overall_quality_score=overall_quality_score
        )


class TestQualityReporter:
    """Generates comprehensive quality reports for test suites."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analyzer = TestQualityAnalyzer(project_root)

    def generate_project_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate a comprehensive quality report for the entire project."""
        print("📊 Generating project-wide test quality report...")

        # Find all test files, excluding virtual environment and node_modules
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            for test_file in self.project_root.rglob(pattern):
                # Skip virtual environment and node_modules
                if any(skip in str(test_file) for skip in ['.venv', 'node_modules', '__pycache__']):
                    continue
                # Only include files in the project (not external packages)
                if self.project_root in test_file.parents:
                    test_files.append(test_file)

        if not test_files:
            return {"error": "No test files found"}

        # Analyze each test file
        all_metrics = []
        all_issues = []

        for test_file in test_files:
            metrics, issues = self.analyzer.analyze_test_file(test_file)
            metrics.file_path = str(test_file)
            all_metrics.append(metrics)
            all_issues.extend(issues)

        # Calculate project-wide metrics
        project_metrics = self._calculate_project_metrics(all_metrics)

        # Generate issue summary
        issue_summary = self._summarize_issues(all_issues)

        # Generate recommendations
        recommendations = self._generate_recommendations(project_metrics, issue_summary)

        report = {
            "project_path": str(self.project_root),
            "test_files_analyzed": len(test_files),
            "project_metrics": asdict(project_metrics),
            "file_metrics": [asdict(m) for m in all_metrics],
            "issue_summary": issue_summary,
            "recommendations": recommendations,
            "quality_grade": self._calculate_quality_grade(project_metrics.overall_quality_score)
        }

        # Save report if output path specified
        if output_path:
            self._save_report(report, output_path)
            print(f"📁 Report saved to: {output_path}")

        return report

    def _calculate_project_metrics(self, file_metrics: List[QualityMetrics]) -> QualityMetrics:
        """Calculate project-wide metrics from file metrics."""
        if not file_metrics:
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0)

        # Average all metrics
        totals = QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0)

        for metric in file_metrics:
            totals.business_logic_coverage += metric.business_logic_coverage
            totals.error_scenario_coverage += metric.error_scenario_coverage
            totals.mock_isolation_score += metric.mock_isolation_score
            totals.realistic_data_score += metric.realistic_data_score
            totals.test_complexity_score += metric.test_complexity_score
            totals.documentation_quality += metric.documentation_quality
            totals.maintenance_score += metric.maintenance_score
            totals.overall_quality_score += metric.overall_quality_score

        count = len(file_metrics)
        return QualityMetrics(
            business_logic_coverage=totals.business_logic_coverage / count,
            error_scenario_coverage=totals.error_scenario_coverage / count,
            mock_isolation_score=totals.mock_isolation_score / count,
            realistic_data_score=totals.realistic_data_score / count,
            test_complexity_score=totals.test_complexity_score / count,
            documentation_quality=totals.documentation_quality / count,
            maintenance_score=totals.maintenance_score / count,
            overall_quality_score=totals.overall_quality_score / count
        )

    def _summarize_issues(self, issues: List[TestQualityIssue]) -> Dict[str, Any]:
        """Summarize issues by severity and category."""
        summary = {
            "total_issues": len(issues),
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_category": {},
            "most_common_issues": []
        }

        for issue in issues:
            summary["by_severity"][issue.severity] += 1

            if issue.category not in summary["by_category"]:
                summary["by_category"][issue.category] = 0
            summary["by_category"][issue.category] += 1

        # Find most common issues
        category_counts = summary["by_category"]
        if category_counts:
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            summary["most_common_issues"] = sorted_categories[:5]

        return summary

    def _generate_recommendations(self, metrics: QualityMetrics, issue_summary: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Business logic recommendations
        if metrics.business_logic_coverage < 70:
            recommendations.append(
                f"🎯 Improve business logic coverage (current: {metrics.business_logic_coverage:.1f}%). "
                "Add tests that verify actual business rules and decision logic."
            )

        # Error scenario recommendations
        if metrics.error_scenario_coverage < 60:
            recommendations.append(
                f"⚠️  Add more error scenario tests (current: {metrics.error_scenario_coverage:.1f}%). "
                "Test failure conditions, edge cases, and error handling."
            )

        # Mock isolation recommendations
        if metrics.mock_isolation_score < 70:
            recommendations.append(
                f"🔧 Improve test isolation (current: {metrics.mock_isolation_score:.1f}%). "
                "Add proper mocking for external dependencies."
            )

        # Data quality recommendations
        if metrics.realistic_data_score < 60:
            recommendations.append(
                f"📊 Use more realistic test data (current: {metrics.realistic_data_score:.1f}%). "
                "Create meaningful test fixtures and sample data."
            )

        # Documentation recommendations
        if metrics.documentation_quality < 80:
            recommendations.append(
                f"📝 Improve test documentation (current: {metrics.documentation_quality:.1f}%). "
                "Add descriptive docstrings to test functions."
            )

        # Issue-based recommendations
        if issue_summary["by_severity"]["critical"] > 0:
            recommendations.append(
                f"🚨 Address {issue_summary['by_severity']['critical']} critical issues immediately."
            )

        if issue_summary["by_severity"]["high"] > 0:
            recommendations.append(
                f"⚡ Prioritize fixing {issue_summary['by_severity']['high']} high-severity issues."
            )

        return recommendations

    def _calculate_quality_grade(self, overall_score: float) -> str:
        """Calculate quality grade based on overall score."""
        if overall_score >= 90:
            return "A+ (Excellent)"
        elif overall_score >= 80:
            return "A (Very Good)"
        elif overall_score >= 70:
            return "B (Good)"
        elif overall_score >= 60:
            return "C (Fair)"
        elif overall_score >= 50:
            return "D (Poor)"
        else:
            return "F (Very Poor)"

    def _save_report(self, report: Dict[str, Any], output_path: Path):
        """Save the quality report to file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            print(f"❌ Error saving report: {e}")

    def print_summary_report(self, report: Dict[str, Any]):
        """Print a human-readable summary of the quality report."""
        print("\n" + "="*60)
        print("📊 TEST QUALITY REPORT")
        print("="*60)

        print(f"\n📁 Project: {report['project_path']}")
        print(f"📄 Test files analyzed: {report['test_files_analyzed']}")
        print(f"🏆 Quality Grade: {report['quality_grade']}")

        metrics = report['project_metrics']
        print(f"\n📈 Overall Quality Score: {metrics.overall_quality_score:.1f}%")

        print("\n📋 Detailed Metrics:")
        print(f"  • Business Logic Coverage: {metrics.business_logic_coverage:.1f}%")
        print(f"  • Error Scenario Coverage: {metrics.error_scenario_coverage:.1f}%")
        print(f"  • Mock Isolation Score: {metrics.mock_isolation_score:.1f}%")
        print(f"  • Realistic Data Score: {metrics.realistic_data_score:.1f}%")
        print(f"  • Documentation Quality: {metrics.documentation_quality:.1f}%")
        print(f"  • Maintenance Score: {metrics.maintenance_score:.1f}%")

        issue_summary = report['issue_summary']
        print(f"\n🚨 Issues Found: {issue_summary['total_issues']}")
        print(f"  • Critical: {issue_summary['by_severity']['critical']}")
        print(f"  • High: {issue_summary['by_severity']['high']}")
        print(f"  • Medium: {issue_summary['by_severity']['medium']}")
        print(f"  • Low: {issue_summary['by_severity']['low']}")

        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")

        print("\n" + "="*60)


class TestQualityValidator:
    """Validates test quality against defined standards."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.quality_thresholds = {
            "business_logic_coverage": 70.0,
            "error_scenario_coverage": 60.0,
            "mock_isolation_score": 70.0,
            "realistic_data_score": 60.0,
            "overall_quality_score": 75.0
        }

    def validate_quality(self, test_file: Path) -> Dict[str, Any]:
        """Validate a test file against quality standards."""
        analyzer = TestQualityAnalyzer(self.project_root)
        metrics, issues = analyzer.analyze_test_file(test_file)

        validation_result = {
            "file_path": str(test_file),
            "passed": True,
            "metrics": asdict(metrics),
            "issues": [asdict(issue) for issue in issues],
            "failed_thresholds": []
        }

        # Check against quality thresholds
        for metric, threshold in self.quality_thresholds.items():
            value = getattr(metrics, metric)
            if value < threshold:
                validation_result["passed"] = False
                validation_result["failed_thresholds"].append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "gap": threshold - value
                })

        return validation_result

    def validate_project(self) -> Dict[str, Any]:
        """Validate the entire project against quality standards."""
        print("🔍 Validating project test quality...")

        # Find all test files, excluding virtual environment and node_modules
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            for test_file in self.project_root.rglob(pattern):
                # Skip virtual environment and node_modules
                if any(skip in str(test_file) for skip in ['.venv', 'node_modules', '__pycache__']):
                    continue
                # Only include files in the project (not external packages)
                if self.project_root in test_file.parents:
                    test_files.append(test_file)

        if not test_files:
            return {"error": "No test files found"}

        # Validate each file
        all_results = []
        project_passed = True

        for test_file in test_files:
            result = self.validate_quality(test_file)
            all_results.append(result)
            if not result["passed"]:
                project_passed = False

        # Calculate project validation summary
        passed_files = sum(1 for result in all_results if result["passed"])

        project_result = {
            "project_path": str(self.project_root),
            "validation_passed": project_passed,
            "files_validated": len(all_results),
            "files_passed": passed_files,
            "files_failed": len(all_results) - passed_files,
            "pass_rate": (passed_files / len(all_results)) * 100 if all_results else 0,
            "file_results": all_results
        }

        return project_result


class TestQualityCommand:
    """CLI commands for test quality validation and reporting."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reporter = TestQualityReporter(project_root)
        self.validator = TestQualityValidator(project_root)

    def run_quality_check(self, file_path: Optional[Path] = None) -> int:
        """Run quality check on specific file or entire project."""
        if file_path:
            print(f"🔍 Running quality check on: {file_path}")
            result = self.validator.validate_quality(file_path)

            if result["passed"]:
                print(f"✅ {file_path} passed quality validation")
                print(f"📊 Overall score: {result['metrics']['overall_quality_score']:.1f}%")
            else:
                print(f"❌ {file_path} failed quality validation")
                for failed in result["failed_thresholds"]:
                    print(f"  • {failed['metric']}: {failed['value']:.1f}% < {failed['threshold']:.1f}%")

            return 0 if result["passed"] else 1
        else:
            print("🔍 Running project-wide quality validation...")
            result = self.validator.validate_project()

            if result["validation_passed"]:
                print(f"✅ Project passed quality validation")
                print(f"📊 Pass rate: {result['pass_rate']:.1f}% ({result['files_passed']}/{result['files_validated']})")
            else:
                print(f"❌ Project failed quality validation")
                print(f"📊 Pass rate: {result['pass_rate']:.1f}% ({result['files_passed']}/{result['files_validated']})")

            return 0 if result["validation_passed"] else 1

    def generate_report(self, output_path: Optional[Path] = None, print_summary: bool = True) -> int:
        """Generate comprehensive quality report."""
        report = self.reporter.generate_project_report(output_path)

        if "error" in report:
            print(f"❌ Error generating report: {report['error']}")
            return 1

        if print_summary:
            self.reporter.print_summary_report(report)

        return 0

    def run_coverage_analysis(self) -> int:
        """Run test coverage analysis."""
        print("📊 Running test coverage analysis...")

        try:
            # Run pytest with coverage
            cmd = [
                "python3", "-m", "pytest",
                "--cov=tool_router",
                "--cov-report=json",
                "--cov-report=html",
                "--cov-report=term-missing",
                "tool_router/tests/"
            ]

            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Coverage analysis completed")
                print(result.stdout)

                # Try to read coverage report
                coverage_file = self.project_root / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file, 'r') as f:
                        coverage_data = json.load(f)

                    total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                    print(f"\n📊 Total Coverage: {total_coverage:.1f}%")

                    if total_coverage < 80:
                        print("⚠️  Coverage below 80% - consider adding more tests")
                else:
                    print("⚠️  Coverage report not found")

                return 0
            else:
                print(f"❌ Coverage analysis failed: {result.stderr}")
                return 1

        except Exception as e:
            print(f"❌ Error running coverage analysis: {e}")
            return 1


def validate_project_path(path_str: str) -> Path:
    """Validate and resolve project path to prevent path traversal."""
    path = Path(path_str).resolve()

    # Ensure the path is within reasonable bounds
    try:
        # Convert to absolute path and check it doesn't go outside current working directory
        cwd = Path.cwd().resolve()
        if not str(path).startswith(str(cwd)):
            # If path tries to go outside current directory, use current directory
            return cwd
        return path
    except (ValueError, OSError):
        # If path is invalid, use current directory
        return Path.cwd()


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Test Quality Validation and Reporting Tools")
    parser.add_argument("command", choices=["check", "report", "coverage"],
                       help="Command to run")
    parser.add_argument("--file", help="Specific test file to check")
    parser.add_argument("--output", help="Output file for reports")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--no-summary", action="store_true", help="Don't print summary report")

    args = parser.parse_args()

    project_root = validate_project_path(args.project_root)
    command = TestQualityCommand(project_root)

    if args.command == "check":
        file_path = Path(args.file) if args.file else None
        return command.run_quality_check(file_path)

    elif args.command == "report":
        output_path = Path(args.output) if args.output else None
        print_summary = not args.no_summary
        return command.generate_report(output_path, print_summary)

    elif args.command == "coverage":
        return command.run_coverage_analysis()

    return 0


if __name__ == "__main__":
    sys.exit(main())
