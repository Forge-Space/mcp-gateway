#!/usr/bin/env python3
"""
Test Quality Validation Tools and Commands

Implements quality validation, analysis, and reporting tools
for the MCP Gateway test creation workflows.
"""

import ast
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import re


@dataclass
class TestQualityMetrics:
    """Metrics for test quality analysis"""
    total_tests: int
    business_logic_tests: int
    trivial_tests: int
    integration_tests: int
    coverage_percentage: float
    false_positive_risk: float
    quality_score: float


@dataclass
class TestIssue:
    """Represents a test quality issue"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'


class TestQualityAnalyzer:
    """Analyzes test quality and identifies issues"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.test_dir = self.project_root / "tool_router" / "tests"
        self.issues: List[TestIssue] = []

        # Patterns that indicate low-quality tests
        self.trivial_patterns = [
            r"assert\s+.*\s*==\s*True",  # Asserting True/False
            r"assert\s+.*\s*==\s*False",
            r"assert\s+.*\s*==\s*None",   # Asserting None
            r"assert\s+.*\s*==\s*\[\]",    # Asserting empty list
            r"assert\s+.*\s*==\s*\{\}",    # Asserting empty dict
            r"test_.*_enum",               # Testing enum values
            r"test_.*_constant",           # Testing constants
            r"test_.*_getter",             # Testing getters
            r"test_.*_setter",             # Testing setters
        ]

        # Patterns that indicate good tests
        self.good_patterns = [
            r"assert\s+.*\s*>\s*0",        # Positive assertions
            r"assert\s+.*\s*<\s*0",        # Negative assertions
            r"assert\s+.*\s*>=\s*\d+",     # Threshold assertions
            r"assert\s+.*\s*<=\s*\d+",
            r"mock\.",                      # Proper mocking
            r"patch\.",                     # Patching
            r"with.*mock",                 # Context manager mocks
            r"pytest\.raises",             # Exception testing
            r"assert.*in.*",               # Membership testing
            r"assert.*not in.*",           # Negative membership
        ]

    def analyze_test_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single test file for quality issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}

        tree = ast.parse(content)

        analysis = {
            "file": str(file_path),
            "total_tests": 0,
            "business_logic_tests": 0,
            "trivial_tests": 0,
            "integration_tests": 0,
            "has_mocks": False,
            "has_exception_tests": False,
            "has_edge_cases": False,
            "test_names": [],
            "issues": []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                analysis["total_tests"] += 1
                analysis["test_names"].append(node.name)

                # Analyze test function content
                test_content = ast.get_source_segment(content, node) or ""

                # Check for trivial patterns
                if any(re.search(pattern, test_content, re.IGNORECASE) for pattern in self.trivial_patterns):
                    analysis["trivial_tests"] += 1
                    analysis["issues"].append({
                        "type": "trivial_test",
                        "function": node.name,
                        "description": "Test appears to test trivial functionality"
                    })

                # Check for good patterns
                if any(re.search(pattern, test_content, re.IGNORECASE) for pattern in self.good_patterns):
                    analysis["business_logic_tests"] += 1

                # Check for mocking
                if "mock" in test_content.lower() or "patch" in test_content.lower():
                    analysis["has_mocks"] = True

                # Check for exception testing
                if "pytest.raises" in test_content or "raises" in test_content:
                    analysis["has_exception_tests"] = True

                # Check for edge cases
                edge_case_indicators = ["empty", "none", "null", "invalid", "error", "exception", "boundary"]
                if any(indicator in test_content.lower() for indicator in edge_case_indicators):
                    analysis["has_edge_cases"] = True

                # Check for integration test indicators
                integration_indicators = ["integration", "workflow", "end_to_end", "e2e", "system"]
                if any(indicator in node.name.lower() for indicator in integration_indicators):
                    analysis["integration_tests"] += 1

        return analysis

    def analyze_project_coverage(self) -> Dict[str, Any]:
        """Run coverage analysis and return results"""
        try:
            # Run coverage report
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=tool_router", "--cov-report=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return {"error": "Coverage analysis failed", "stderr": result.stderr}

            # Parse coverage JSON
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                return coverage_data
            else:
                return {"error": "Coverage file not generated"}

        except subprocess.TimeoutExpired:
            return {"error": "Coverage analysis timed out"}
        except Exception as e:
            return {"error": f"Coverage analysis failed: {str(e)}"}

    def calculate_quality_metrics(self, analyses: List[Dict[str, Any]], coverage_data: Dict[str, Any]) -> TestQualityMetrics:
        """Calculate overall quality metrics"""
        total_tests = sum(a.get("total_tests", 0) for a in analyses)
        business_logic_tests = sum(a.get("business_logic_tests", 0) for a in analyses)
        trivial_tests = sum(a.get("trivial_tests", 0) for a in analyses)
        integration_tests = sum(a.get("integration_tests", 0) for a in analyses)

        # Get overall coverage percentage
        coverage_percentage = 0.0
        if "totals" in coverage_data:
            coverage_percentage = coverage_data["totals"].get("percent_covered", 0.0)

        # Calculate false positive risk (percentage of trivial tests)
        false_positive_risk = (trivial_tests / total_tests * 100) if total_tests > 0 else 0.0

        # Calculate quality score (0-100)
        # Factors: business logic tests, coverage, integration tests, low trivial test ratio
        business_score = (business_logic_tests / total_tests * 50) if total_tests > 0 else 0
        coverage_score = min(coverage_percentage * 0.3, 30)  # Max 30 points
        integration_score = min(integration_tests / total_tests * 20, 20) if total_tests > 0 else 0
        trivial_penalty = min(false_positive_risk * 0.5, 20)  # Penalty up to 20 points

        quality_score = business_score + coverage_score + integration_score - trivial_penalty
        quality_score = max(0, min(100, quality_score))  # Clamp to 0-100

        return TestQualityMetrics(
            total_tests=total_tests,
            business_logic_tests=business_logic_tests,
            trivial_tests=trivial_tests,
            integration_tests=integration_tests,
            coverage_percentage=coverage_percentage,
            false_positive_risk=false_positive_risk,
            quality_score=quality_score
        )

    def generate_report(self, metrics: TestQualityMetrics, analyses: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive quality report"""
        report = []
        report.append("# Test Quality Analysis Report")
        report.append(f"Generated: {__import__('datetime').datetime.now().isoformat()}")
        report.append("")

        # Executive Summary
        report.append("## Executive Summary")
        report.append(f"- **Total Tests**: {metrics.total_tests}")
        report.append(f"- **Business Logic Tests**: {metrics.business_logic_tests}")
        report.append(f"- **Trivial Tests**: {metrics.trivial_tests}")
        report.append(f"- **Integration Tests**: {metrics.integration_tests}")
        report.append(f"- **Coverage**: {metrics.coverage_percentage:.2f}%")
        report.append(f"- **False Positive Risk**: {metrics.false_positive_risk:.2f}%")
        report.append(f"- **Quality Score**: {metrics.quality_score:.2f}/100")
        report.append("")

        # Quality Assessment
        report.append("## Quality Assessment")
        if metrics.quality_score >= 80:
            report.append("🟢 **EXCELLENT** - High quality test suite")
        elif metrics.quality_score >= 60:
            report.append("🟡 **GOOD** - Acceptable quality with room for improvement")
        elif metrics.quality_score >= 40:
            report.append("🟠 **FAIR** - Quality issues need attention")
        else:
            report.append("🔴 **POOR** - Significant quality issues")
        report.append("")

        # Coverage Analysis
        report.append("## Coverage Analysis")
        if metrics.coverage_percentage >= 80:
            report.append("✅ Coverage meets target (≥80%)")
        elif metrics.coverage_percentage >= 60:
            report.append("⚠️ Coverage is below target (≥80%)")
        else:
            report.append("❌ Coverage is significantly below target")
        report.append("")

        # Recommendations
        report.append("## Recommendations")
        recommendations = []

        if metrics.false_positive_risk > 20:
            recommendations.append("- **High Priority**: Reduce trivial tests ({:.1f}% false positive risk)".format(metrics.false_positive_risk))

        if metrics.coverage_percentage < 80:
            recommendations.append("- **High Priority**: Increase coverage to 80%+ (currently {:.1f}%)".format(metrics.coverage_percentage))

        if metrics.integration_tests < 5:
            recommendations.append("- **Medium Priority**: Add more integration tests")

        if metrics.business_logic_tests / max(metrics.total_tests, 1) < 0.5:
            recommendations.append("- **Medium Priority**: Focus on business logic testing")

        if not recommendations:
            recommendations.append("- **Good**: Test quality is acceptable")

        report.extend(recommendations)
        report.append("")

        # Detailed Analysis
        report.append("## Detailed Analysis")
        for analysis in analyses:
            if "error" in analysis:
                continue

            file_path = analysis["file"]
            report.append(f"### {file_path}")
            report.append(f"- Tests: {analysis['total_tests']}")
            report.append(f"- Business Logic: {analysis['business_logic_tests']}")
            report.append(f"- Trivial: {analysis['trivial_tests']}")
            report.append(f"- Integration: {analysis['integration_tests']}")

            if analysis["issues"]:
                report.append("- Issues:")
                for issue in analysis["issues"]:
                    report.append(f"  - {issue['type']}: {issue['function']} - {issue['description']}")
            report.append("")

        return "\n".join(report)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Quality Validation Tool")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--threshold", type=float, default=80.0, help="Coverage threshold")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = TestQualityAnalyzer(args.project_root)

    # Find all test files
    test_files = []
    if analyzer.test_dir.exists():
        test_files.extend(list(analyzer.test_dir.rglob("test_*.py")))

    if not test_files:
        print("No test files found!")
        return 1

    # Analyze test files
    print(f"Analyzing {len(test_files)} test files...")
    analyses = []
    for test_file in test_files:
        if args.verbose:
            print(f"  Analyzing {test_file}")
        analysis = analyzer.analyze_test_file(test_file)
        analyses.append(analysis)

    # Run coverage analysis
    print("Running coverage analysis...")
    coverage_data = analyzer.analyze_project_coverage()

    # Calculate metrics
    metrics = analyzer.calculate_quality_metrics(analyses, coverage_data)

    # Generate report
    report = analyzer.generate_report(metrics, analyses)

    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)

    # Exit with appropriate code
    if metrics.quality_score < 40 or metrics.coverage_percentage < args.threshold:
        return 1  # Failure
    return 0


if __name__ == "__main__":
    sys.exit(main())
