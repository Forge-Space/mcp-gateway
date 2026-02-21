#!/usr/bin/env python3
"""
Coordinated Release Testing Script

Tests the automated release pipeline coordination across all Forge ecosystem repositories.
Validates that repository dispatch events are properly configured and can trigger cross-repository workflows.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

class CoordinatedReleaseTester:
    def __init__(self):
        self.repositories = {
            'forge-patterns': '/Users/lucassantana/Desenvolvimento/forge-patterns',
            'mcp-gateway': '/Users/lucassantana/Desenvolvimento/mcp-gateway',
            'uiforge-mcp': '/Users/lucassantana/Desenvolvimento/uiforge-mcp',
            'uiforge-webapp': '/Users/lucassantana/Desenvolvimento/uiforge-webapp'
        }
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'passed': passed
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")

    def check_repository_structure(self, repo_name: str, repo_path: str) -> bool:
        """Check if repository has the required structure"""
        required_files = [
            '.github/workflows/release-automation.yml',
            '.github/workflows/branch-protection.yml',
            'README.md',
            'package.json' if repo_name != 'mcp-gateway' else 'pyproject.toml'
        ]

        missing_files = []
        for file_path in required_files:
            full_path = Path(repo_path) / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            return False, f"Missing files: {', '.join(missing_files)}"

        return True, "All required files present"

    def validate_release_workflow(self, repo_name: str, repo_path: str) -> bool:
        """Validate the release-automation.yml workflow"""
        workflow_path = Path(repo_path) / '.github/workflows/release-automation.yml'

        if not workflow_path.exists():
            return False, "release-automation.yml not found"

        try:
            with open(workflow_path, 'r') as f:
                content = f.read()

            # Check for required components
            required_components = [
                'on:', 'push:', 'branches:', 'main',
                'jobs:', 'quality-gates:', 'build-test:', 'release:',
                'repository-dispatch'
            ]

            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)

            if missing_components:
                return False, f"Missing workflow components: {', '.join(missing_components)}"

            return True, "Release workflow properly configured"

        except Exception as e:
            return False, f"Error reading workflow file: {str(e)}"

    def validate_repository_dispatch(self, repo_name: str, repo_path: str) -> bool:
        """Validate repository dispatch configuration"""
        workflow_path = Path(repo_path) / '.github/workflows/release-automation.yml'

        if not workflow_path.exists():
            return False, "release-automation.yml not found"

        try:
            with open(workflow_path, 'r') as f:
                content = f.read()

            # Check for repository dispatch configuration
            if 'repository-dispatch' not in content:
                return False, "Repository dispatch not configured"

            if 'event-type: release-published' not in content:
                return False, "Release-published event type not configured"

            # Extract repository dispatch target
            lines = content.split('\n')
            dispatch_config = {}

            for i, line in enumerate(lines):
                if 'repository:' in line and any('repository-dispatch' in ctx_line for ctx_line in lines[i-5:i+5]):
                    dispatch_config['target'] = line.split(':')[1].strip()
                elif 'event-type:' in line and any('repository-dispatch' in ctx_line for ctx_line in lines[i-5:i+5]):
                    dispatch_config['event_type'] = line.split(':')[1].strip()
                elif 'client-payload:' in line and any('repository-dispatch' in ctx_line for ctx_line in lines[i-5:i+5]):
                    # Extract client payload structure
                    payload_lines = []
                    indent_level = len(line) - len(line.lstrip())

                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() == '':
                            continue
                        if len(lines[j]) - len(lines[j].lstrip()) <= indent_level and lines[j].strip().startswith('}'):
                            payload_lines.append(lines[j])
                            break
                        payload_lines.append(lines[j])

                    dispatch_config['payload'] = '\n'.join(payload_lines)

            if not dispatch_config.get('target'):
                return False, "Repository dispatch target not configured"

            return True, f"Repository dispatch configured for {dispatch_config.get('target')}"

        except Exception as e:
            return False, f"Error validating repository dispatch: {str(e)}"

    def check_branch_protection(self, repo_name: str, repo_path: str) -> bool:
        """Check branch protection workflow"""
        workflow_path = Path(repo_path) / '.github/workflows/branch-protection.yml'

        if not workflow_path.exists():
            return False, "branch-protection.yml not found"

        try:
            with open(workflow_path, 'r') as f:
                content = f.read()

            required_jobs = ['pre-commit', 'release-validation', 'docs-validation']
            missing_jobs = []

            for job in required_jobs:
                if job not in content:
                    missing_jobs.append(job)

            if missing_jobs:
                return False, f"Missing branch protection jobs: {', '.join(missing_jobs)}"

            return True, "Branch protection workflow properly configured"

        except Exception as e:
            return False, f"Error checking branch protection: {str(e)}"

    def validate_package_configuration(self, repo_name: str, repo_path: str) -> bool:
        """Validate package configuration for publishing"""
        if repo_name == 'mcp-gateway':
            config_file = Path(repo_path) / 'pyproject.toml'
            if not config_file.exists():
                return False, "pyproject.toml not found"

            try:
                with open(config_file, 'r') as f:
                    content = f.read()

                if 'version' not in content:
                    return False, "Version not configured in pyproject.toml"

                return True, "Python package properly configured"

            except Exception as e:
                return False, f"Error reading pyproject.toml: {str(e)}"

        else:
            config_file = Path(repo_path) / 'package.json'
            if not config_file.exists():
                return False, "package.json not found"

            try:
                with open(config_file, 'r') as f:
                    package_data = json.load(f)

                required_fields = ['name', 'version', 'scripts']
                missing_fields = []

                for field in required_fields:
                    if field not in package_data:
                        missing_fields.append(field)

                if missing_fields:
                    return False, f"Missing package.json fields: {', '.join(missing_fields)}"

                return True, f"Package {package_data.get('name')} properly configured"

            except Exception as e:
                return False, f"Error reading package.json: {str(e)}"

    def test_coordinated_release_flow(self) -> bool:
        """Test the complete coordinated release flow"""
        print("🚀 Testing Coordinated Release Flow Across Forge Ecosystem")
        print("=" * 60)

        # Test each repository
        for repo_name, repo_path in self.repositories.items():
            print(f"\n📦 Testing {repo_name}")
            print("-" * 40)

            # Check repository structure
            passed, message = self.check_repository_structure(repo_name, repo_path)
            self.log_test(f"{repo_name} - Repository Structure", passed, message)

            # Validate release workflow
            passed, message = self.validate_release_workflow(repo_name, repo_path)
            self.log_test(f"{repo_name} - Release Workflow", passed, message)

            # Validate repository dispatch
            passed, message = self.validate_repository_dispatch(repo_name, repo_path)
            self.log_test(f"{repo_name} - Repository Dispatch", passed, message)

            # Check branch protection
            passed, message = self.check_branch_protection(repo_name, repo_path)
            self.log_test(f"{repo_name} - Branch Protection", passed, message)

            # Validate package configuration
            passed, message = self.validate_package_configuration(repo_name, repo_path)
            self.log_test(f"{repo_name} - Package Configuration", passed, message)

        # Test cross-repository coordination
        print(f"\n🔗 Testing Cross-Repository Coordination")
        print("-" * 40)

        # Check if all repositories can trigger dispatch events
        dispatch_targets = set()
        for repo_name, repo_path in self.repositories.items():
            workflow_path = Path(repo_path) / '.github/workflows/release-automation.yml'
            if workflow_path.exists():
                try:
                    with open(workflow_path, 'r') as f:
                        content = f.read()

                    # Extract repository dispatch targets
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'repository:' in line and any(
                            'repository-dispatch' in lines[j]
                            for j in range(max(0, i-10), i)
                        ):
                            target = line.split(':')[1].strip()
                            dispatch_targets.add(target)
                except:
                    pass

        if len(dispatch_targets) > 0:
            self.log_test("Cross-Repository Dispatch", True, f"Dispatch targets: {', '.join(dispatch_targets)}")
        else:
            self.log_test("Cross-Repository Dispatch", False, "No repository dispatch targets found")

        # Generate summary report
        self.generate_summary_report()

        return all(result['passed'] for result in self.test_results)

    def generate_summary_report(self):
        """Generate a summary report of the test results"""
        print(f"\n📊 Coordinated Release Test Summary")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  • {result['test']}: {result['message']}")

        print(f"\n🎯 Recommendations:")
        if failed_tests == 0:
            print("  ✅ All repositories are ready for coordinated releases!")
            print("  ✅ Repository dispatch events are properly configured")
            print("  ✅ Quality gates and branch protection are in place")
        else:
            print("  🔧 Fix failed tests before enabling coordinated releases")
            print("  🔧 Ensure all repository workflows have proper dispatch configuration")
            print("  🔧 Validate package configurations for all repositories")

        # Save detailed report
        report_file = Path('/Users/lucassantana/Desenvolvimento/mcp-gateway') / 'coordinated-release-test-report.json'
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': str(Path.cwd()),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests/total_tests)*100,
                'results': self.test_results
            }, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main function to run the coordinated release testing"""
    tester = CoordinatedReleaseTester()
    success = tester.test_coordinated_release_flow()

    if success:
        print(f"\n🎉 Coordinated release testing completed successfully!")
        print(f"🚀 All Forge ecosystem repositories are ready for automated releases!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Coordinated release testing completed with issues.")
        print(f"🔧 Please address the failed tests before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
