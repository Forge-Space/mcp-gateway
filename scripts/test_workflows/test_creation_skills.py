#!/usr/bin/env python3
"""
Test Creation Skills - Reusable Functions for High-Quality Test Generation

Implements the test creation skills defined in the plan:
- Business Logic Testing
- Mocking and Test Isolation  
- Error Scenario Testing
- Test Data Design

Quality Over Quantity: Every function creates tests that provide real confidence.
"""

import ast
import inspect
import textwrap
import sys
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestTemplate:
    """Template for generating test code."""
    name: str
    description: str
    template_code: str
    variables: Dict[str, Any]
    quality_score: float


class BusinessLogicTestingSkill:
    """Skill for creating tests that verify actual business logic and system behavior."""
    
    def __init__(self):
        self.business_indicators = {
            'decision_logic': ['if', 'elif', 'else', 'switch', 'case'],
            'loops': ['for', 'while', 'do', 'foreach'],
            'error_handling': ['try', 'except', 'catch', 'finally', 'raise'],
            'data_processing': ['map', 'filter', 'reduce', 'transform', 'process'],
            'calculations': ['calculate', 'compute', 'evaluate', 'determine'],
            'validations': ['validate', 'verify', 'check', 'ensure', 'assert']
        }
    
    def analyze_business_logic(self, function_code: str) -> Dict[str, Any]:
        """Analyze function code to identify business logic patterns."""
        analysis = {
            "has_decision_logic": False,
            "has_loops": False,
            "has_error_handling": False,
            "has_data_processing": False,
            "has_calculations": False,
            "has_validations": False,
            "complexity_score": 0.0,
            "business_value": "low"
        }
        
        # Check for business logic indicators
        lines = function_code.lower().split('\n')
        for line in lines:
            for category, indicators in self.business_indicators.items():
                if any(indicator in line for indicator in indicators):
                    analysis[f"has_{category}"] = True
                    analysis["complexity_score"] += 1.0
        
        # Determine business value
        if analysis["complexity_score"] >= 3:
            analysis["business_value"] = "high"
        elif analysis["complexity_score"] >= 1:
            analysis["business_value"] = "medium"
        
        return analysis
    
    def generate_business_logic_test(self, function_name: str, analysis: Dict[str, Any]) -> TestTemplate:
        """Generate a test that focuses on business logic."""
        if analysis["business_value"] == "low":
            return None
        
        test_code = f"""
    def test_{function_name}_business_logic(self) -> None:
        \"\"\"Test the core business logic of {function_name}.\"\"\"
        # Test the primary business outcome
        result = {function_name}(valid_input_data)
        
        # Verify business rules are applied correctly
        assert result is not None
        assert isinstance(result, expected_type)
        
        # Test business decision logic
        if hasattr(result, 'status'):
            assert result.status in ['approved', 'rejected', 'pending']
        
        # Test data processing accuracy
        if hasattr(result, 'processed_data'):
            assert len(result.processed_data) > 0
            assert all(item is not None for item in result.processed_data)
"""
        
        if analysis["has_error_handling"]:
            test_code += f"""
        
        # Test error handling in business logic
        with pytest.raises(BusinessLogicError):
            {function_name}(invalid_input_data)
"""
        
        return TestTemplate(
            name=f"test_{function_name}_business_logic",
            description=f"Test core business logic of {function_name}",
            template_code=test_code.strip(),
            variables={"function_name": function_name, "analysis": analysis},
            quality_score=85.0 + (analysis["complexity_score"] * 5)
        )
    
    def create_realistic_test_data(self, function_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create realistic test data that mirrors production scenarios."""
        data_templates = {
            "user_data": {
                "valid_user": {
                    "id": 12345,
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "role": "user",
                    "active": True,
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "admin_user": {
                    "id": 67890,
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com",
                    "role": "admin",
                    "active": True,
                    "permissions": ["read", "write", "delete"]
                }
            },
            "api_data": {
                "success_response": {
                    "status": "success",
                    "data": {"result": "operation_completed"},
                    "timestamp": "2024-02-20T13:06:00Z"
                },
                "error_response": {
                    "status": "error",
                    "error": "Invalid input provided",
                    "code": 400
                }
            },
            "tool_data": {
                "web_search_tool": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "minLength": 1},
                            "max_results": {"type": "integer", "minimum": 1, "maximum": 50}
                        },
                        "required": ["query"]
                    }
                },
                "file_reader_tool": {
                    "name": "file_reader",
                    "description": "Read contents from local files",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "encoding": {"type": "string", "enum": ["utf-8", "latin-1"]}
                        },
                        "required": ["path"]
                    }
                }
            }
        }
        
        # Select appropriate data based on function context
        context_type = function_context.get("type", "general")
        
        if context_type in data_templates:
            return data_templates[context_type]
        else:
            return data_templates["tool_data"]  # Default for MCP tools


class MockingAndTestIsolationSkill:
    """Skill for properly mocking external dependencies to create isolated, reliable tests."""
    
    def __init__(self):
        self.mock_patterns = {
            "http_calls": ["requests.", "httpx.", "aiohttp.", "urllib."],
            "database": ["sqlalchemy.", "psycopg2.", "sqlite3.", "redis.", "pymongo."],
            "file_system": ["open(", "Path(", "os.path.", "shutil."],
            "external_apis": ["requests.get", "requests.post", "httpx.Client", "aiohttp.ClientSession"],
            "time_functions": ["time.time", "datetime.now", "time.sleep"],
            "environment": ["os.environ", "sys.getenv", "config.get"]
        }
    
    def identify_external_dependencies(self, function_code: str) -> List[Dict[str, Any]]:
        """Identify external dependencies that need mocking."""
        dependencies = []
        
        for category, patterns in self.mock_patterns.items():
            for pattern in patterns:
                if pattern in function_code:
                    dependencies.append({
                        "category": category,
                        "pattern": pattern,
                        "mock_type": self._get_mock_type(category),
                        "patch_target": self._get_patch_target(pattern, function_code)
                    })
        
        return dependencies
    
    def _get_mock_type(self, category: str) -> str:
        """Determine the appropriate mock type for a dependency category."""
        mock_types = {
            "http_calls": "AsyncMock" if "async" in category else "MagicMock",
            "database": "MagicMock",
            "file_system": "mock_open",
            "external_apis": "AsyncMock" if "async" in category else "MagicMock",
            "time_functions": "patch",
            "environment": "patch"
        }
        return mock_types.get(category, "MagicMock")
    
    def _get_patch_target(self, pattern: str, function_code: str) -> str:
        """Extract the patch target from function code."""
        lines = function_code.split('\n')
        for line in lines:
            if pattern in line:
                # Try to extract the import path
                if 'import ' in line:
                    return line.split('import ')[1].strip()
                elif 'from ' in line:
                    parts = line.split('from ')[1].split(' import ')
                    return f"{parts[0]}.{parts[1].strip()}"
        return pattern
    
    def generate_mock_setup(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate mock setup code for identified dependencies."""
        if not dependencies:
            return "# No external dependencies to mock"
        
        mock_code = ["# Mock external dependencies"]
        
        for dep in dependencies:
            if dep["mock_type"] == "patch":
                mock_code.append(f"    @patch('{dep['patch_target']}')")
            elif dep["mock_type"] == "mock_open":
                mock_code.append(f"    @patch('builtins.open', new_callable=mock_open)")
            else:
                mock_code.append(f"    @patch('{dep['patch_target']}', new_callable={dep['mock_type']})")
        
        return '\n'.join(mock_code)
    
    def generate_isolated_test(self, function_name: str, dependencies: List[Dict[str, Any]]) -> TestTemplate:
        """Generate a properly isolated test with comprehensive mocking."""
        
        mock_setup = self.generate_mock_setup(dependencies)
        
        test_code = f"""
{mock_setup}
    def test_{function_name}_isolated(self{self._get_mock_params(dependencies)}) -> None:
        \"\"\"Test {function_name} with all external dependencies properly mocked.\"\"\"
        # Configure mocks
{self._configure_mocks(dependencies)}
        
        # Test the function in isolation
        result = {function_name}(test_input_data)
        
        # Verify the result
        assert result is not None
        assert result == expected_result
        
        # Verify mock interactions
{self._verify_mock_interactions(dependencies)}
"""
        
        return TestTemplate(
            name=f"test_{function_name}_isolated",
            description=f"Test {function_name} with proper dependency isolation",
            template_code=test_code.strip(),
            variables={"function_name": function_name, "dependencies": dependencies},
            quality_score=90.0 if dependencies else 70.0
        )
    
    def _get_mock_params(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate mock parameters for test function signature."""
        if not dependencies:
            return ""
        
        param_names = []
        for i, dep in enumerate(dependencies):
            param_name = f"mock_{dep['category']}"
            if param_name not in param_names:
                param_names.append(param_name)
        
        return ", " + ", ".join(param_names)
    
    def _configure_mocks(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate mock configuration code."""
        if not dependencies:
            return "        # No mocks to configure"
        
        config_lines = []
        for dep in dependencies:
            param_name = f"mock_{dep['category']}"
            config_lines.append(f"        {param_name}.return_value = mock_{dep['category']}_data")
        
        return '\n'.join(config_lines)
    
    def _verify_mock_interactions(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate mock verification code."""
        if not dependencies:
            return "        # No mock interactions to verify"
        
        verify_lines = []
        for dep in dependencies:
            param_name = f"mock_{dep['category']}"
            verify_lines.append(f"        {param_name}.assert_called_once()")
        
        return '\n'.join(verify_lines)


class ErrorScenarioTestingSkill:
    """Skill for creating comprehensive tests for error conditions, edge cases, and failure scenarios."""
    
    def __init__(self):
        self.error_scenarios = {
            "network_errors": ["TimeoutException", "ConnectionError", "HTTPError"],
            "data_errors": ["ValueError", "TypeError", "KeyError", "IndexError"],
            "resource_errors": ["FileNotFoundError", "PermissionError", "MemoryError"],
            "business_errors": ["ValidationError", "BusinessLogicError", "AuthenticationError"],
            "system_errors": ["OSError", "RuntimeError", "SystemExit"]
        }
    
    def identify_error_scenarios(self, function_code: str) -> List[Dict[str, Any]]:
        """Identify potential error scenarios in the function."""
        scenarios = []
        
        # Look for explicit error handling
        if 'try:' in function_code and 'except' in function_code:
            scenarios.append({
                "type": "exception_handling",
                "description": "Function has explicit exception handling",
                "test_required": True
            })
        
        # Look for external calls that might fail
        external_patterns = ['.', '(', '[', '{']
        for pattern in external_patterns:
            if pattern in function_code:
                scenarios.append({
                    "type": "external_failure",
                    "description": "Function makes external calls that might fail",
                    "test_required": True
                })
                break
        
        # Look for data processing that might fail
        data_patterns = ['for', 'while', 'map', 'filter', 'list comprehension']
        for pattern in data_patterns:
            if pattern in function_code:
                scenarios.append({
                    "type": "data_processing_error",
                    "description": "Function processes data that might be invalid",
                    "test_required": True
                })
                break
        
        return scenarios
    
    def generate_error_tests(self, function_name: str, scenarios: List[Dict[str, Any]]) -> List[TestTemplate]:
        """Generate comprehensive error scenario tests."""
        tests = []
        
        for scenario in scenarios:
            if scenario["type"] == "exception_handling":
                tests.append(self._generate_exception_test(function_name, scenario))
            elif scenario["type"] == "external_failure":
                tests.append(self._generate_external_failure_test(function_name, scenario))
            elif scenario["type"] == "data_processing_error":
                tests.append(self._generate_data_error_test(function_name, scenario))
        
        return tests
    
    def _generate_exception_test(self, function_name: str, scenario: Dict[str, Any]) -> TestTemplate:
        """Generate test for exception handling."""
        test_code = f"""
    def test_{function_name}_exception_handling(self) -> None:
        \"\"\"Test {function_name} handles exceptions correctly.\"\"\"
        # Test with invalid input that should raise exception
        with pytest.raises((ValueError, TypeError)) as exc_info:
            {function_name}(invalid_input)
        
        # Verify exception details
        assert exc_info.value is not None
        assert str(exc_info.value) != ""
        
        # Test that function doesn't crash completely
        try:
            {function_name}(valid_input)
        except Exception as e:
            pytest.fail(f"Function should not crash with valid input: {{e}}")
"""
        
        return TestTemplate(
            name=f"test_{function_name}_exception_handling",
            description=f"Test exception handling in {function_name}",
            template_code=test_code.strip(),
            variables={"function_name": function_name},
            quality_score=85.0
        )
    
    def _generate_external_failure_test(self, function_name: str, scenario: Dict[str, Any]) -> TestTemplate:
        """Generate test for external service failures."""
        test_code = f"""
    @patch('module.external_service')
    def test_{function_name}_external_failure(self, mock_external) -> None:
        \"\"\"Test {function_name} handles external service failures.\"\"\"
        # Configure mock to raise exception
        mock_external.side_effect = ConnectionError("Service unavailable")
        
        # Test that function handles external failure gracefully
        with pytest.raises(ConnectionError):
            {function_name}(test_input)
        
        # Verify external service was called
        mock_external.assert_called_once()
        
        # Test with timeout
        mock_external.side_effect = TimeoutError("Request timed out")
        with pytest.raises(TimeoutError):
            {function_name}(test_input)
"""
        
        return TestTemplate(
            name=f"test_{function_name}_external_failure",
            description=f"Test external service failure handling in {function_name}",
            template_code=test_code.strip(),
            variables={"function_name": function_name},
            quality_score=90.0
        )
    
    def _generate_data_error_test(self, function_name: str, scenario: Dict[str, Any]) -> TestTemplate:
        """Generate test for data processing errors."""
        test_code = f"""
    def test_{function_name}_data_errors(self) -> None:
        \"\"\"Test {function_name} handles data errors correctly.\"\"\"
        # Test with None input
        with pytest.raises((ValueError, TypeError)):
            {function_name}(None)
        
        # Test with empty data
        result = {function_name}([])
        assert result is not None  # Should handle empty data gracefully
        
        # Test with invalid data types
        with pytest.raises((ValueError, TypeError)):
            {function_name}("invalid_data_type")
        
        # Test with malformed data structure
        with pytest.raises((KeyError, AttributeError)):
            {function_name}({{"invalid": "structure"}})
"""
        
        return TestTemplate(
            name=f"test_{function_name}_data_errors",
            description=f"Test data error handling in {function_name}",
            template_code=test_code.strip(),
            variables={"function_name": function_name},
            quality_score=80.0
        )


class TestDataDesignSkill:
    """Skill for creating meaningful, realistic test data that reflects actual usage scenarios."""
    
    def __init__(self):
        self.data_categories = {
            "mcp_tools": "tools and their schemas",
            "api_responses": "HTTP response data",
            "user_inputs": "user-provided data",
            "system_config": "configuration data",
            "performance_data": "large datasets for performance testing"
        }
    
    def create_test_fixtures(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create reusable test fixtures for the given context."""
        fixtures = {}
        
        context_type = context.get("type", "general")
        
        if context_type == "mcp_tools":
            fixtures.update(self._create_mcp_tool_fixtures())
        elif context_type == "api_responses":
            fixtures.update(self._create_api_response_fixtures())
        elif context_type == "user_inputs":
            fixtures.update(self._create_user_input_fixtures())
        
        # Always add common fixtures
        fixtures.update(self._create_common_fixtures())
        
        return fixtures
    
    def _create_mcp_tool_fixtures(self) -> Dict[str, Any]:
        """Create fixtures specific to MCP tool testing."""
        return {
            "realistic_tools": [
                {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "minLength": 1},
                            "max_results": {"type": "integer", "minimum": 1, "maximum": 50}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "file_reader",
                    "description": "Read contents from local files",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "encoding": {"type": "string", "enum": ["utf-8", "latin-1"]}
                        },
                        "required": ["path"]
                    }
                }
            ],
            "tool_selection_query": "search for python programming tutorials",
            "expected_tool_selection": "web_search"
        }
    
    def _create_api_response_fixtures(self) -> Dict[str, Any]:
        """Create fixtures for API response testing."""
        return {
            "success_response": {
                "status": "success",
                "data": {"result": "operation_completed"},
                "timestamp": "2024-02-20T13:06:00Z",
                "request_id": "req_123456"
            },
            "error_response": {
                "status": "error",
                "error": "Invalid input provided",
                "code": 400,
                "details": {"field": "query", "message": "Required field missing"}
            },
            "paginated_response": {
                "data": [{"id": 1}, {"id": 2}, {"id": 3}],
                "pagination": {
                    "page": 1,
                    "per_page": 10,
                    "total": 25,
                    "has_next": True
                }
            }
        }
    
    def _create_user_input_fixtures(self) -> Dict[str, Any]:
        """Create fixtures for user input testing."""
        return {
            "valid_user_query": "Find information about machine learning",
            "invalid_user_query": "",
            "edge_case_query": "a" * 1000,  # Very long query
            "special_chars_query": "Search for @#$%^&*() special chars",
            "unicode_query": "Search for café résumé naïve"
        }
    
    def _create_common_fixtures(self) -> Dict[str, Any]:
        """Create commonly used test fixtures."""
        return {
            "test_timestamp": "2024-02-20T13:06:00Z",
            "test_user_id": 12345,
            "test_session_id": "sess_abcdef123456",
            "mock_config": {"debug": True, "timeout": 30},
            "empty_result": {"data": [], "count": 0}
        }
    
    def generate_fixture_code(self, fixtures: Dict[str, Any]) -> str:
        """Generate pytest fixture code from fixture definitions."""
        fixture_code = []
        
        for name, data in fixtures.items():
            if isinstance(data, list):
                fixture_code.append(f"""
@pytest.fixture
def {name}() -> list[dict]:
    \"\"\"Provide realistic {name.replace('_', ' ')} for testing.\"\"\"
    return {json.dumps(data, indent=8)}
""")
            elif isinstance(data, dict):
                fixture_code.append(f"""
@pytest.fixture
def {name}() -> dict:
    \"\"\"Provide realistic {name.replace('_', ' ')} for testing.\"\"\"
    return {json.dumps(data, indent=8)}
""")
            else:
                fixture_code.append(f"""
@pytest.fixture
def {name}():
    \"\"\"Provide realistic {name.replace('_', ' ')} for testing.\"\"\"
    return {repr(data)}
""")
        
        return '\n'.join(fixture_code)


class TestSkillOrchestrator:
    """Orchestrates all test creation skills for comprehensive test generation."""
    
    def __init__(self):
        self.business_logic_skill = BusinessLogicTestingSkill()
        self.mocking_skill = MockingAndTestIsolationSkill()
        self.error_skill = ErrorScenarioTestingSkill()
        self.data_skill = TestDataDesignSkill()
    
    def analyze_function(self, function_code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive analysis of a function for test generation."""
        analysis = {
            "business_logic": self.business_logic_skill.analyze_business_logic(function_code),
            "dependencies": self.mocking_skill.identify_external_dependencies(function_code),
            "error_scenarios": self.error_skill.identify_error_scenarios(function_code),
            "context": context
        }
        
        # Calculate overall complexity and test requirements
        analysis["complexity_score"] = (
            analysis["business_logic"]["complexity_score"] +
            len(analysis["dependencies"]) * 2 +
            len(analysis["error_scenarios"]) * 1.5
        )
        
        return analysis
    
    def generate_comprehensive_tests(self, function_name: str, function_code: str, 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive tests using all skills."""
        print(f"🎯 Generating comprehensive tests for {function_name}")
        
        # Analyze the function
        analysis = self.analyze_function(function_code, context)
        
        # Generate test components
        test_components = []
        
        # Business logic tests
        if analysis["business_logic"]["business_value"] != "low":
            business_test = self.business_logic_skill.generate_business_logic_test(
                function_name, analysis["business_logic"]
            )
            if business_test:
                test_components.append(business_test)
        
        # Isolated tests with mocking
        if analysis["dependencies"]:
            isolated_test = self.mocking_skill.generate_isolated_test(
                function_name, analysis["dependencies"]
            )
            test_components.append(isolated_test)
        
        # Error scenario tests
        if analysis["error_scenarios"]:
            error_tests = self.error_skill.generate_error_tests(
                function_name, analysis["error_scenarios"]
            )
            test_components.extend(error_tests)
        
        # Test data fixtures
        fixtures = self.data_skill.create_test_fixtures(context)
        fixture_code = self.data_skill.generate_fixture_code(fixtures)
        
        # Combine all test components
        full_test_code = self._combine_test_components(test_components, fixture_code)
        
        # Calculate quality metrics
        quality_score = self._calculate_quality_score(test_components, analysis)
        
        return {
            "function_name": function_name,
            "analysis": analysis,
            "test_code": full_test_code,
            "test_components": len(test_components),
            "fixtures": fixtures,
            "quality_score": quality_score,
            "recommendations": self._generate_recommendations(analysis)
        }
    
    def _combine_test_components(self, components: List[TestTemplate], fixtures: str) -> str:
        """Combine test components into a complete test file."""
        parts = [
            '"""',
            f'Comprehensive tests generated using test creation skills.',
            f'Quality Over Quantity: Each test provides real confidence.',
            '"""',
            '',
            'import pytest',
            'from unittest.mock import patch, MagicMock, AsyncMock, mock_open',
            'import sys',
            'import os',
            '',
            fixtures,
            ''
        ]
        
        # Add test class
        if components:
            class_name = "TestGenerated"
            parts.append(f"class {class_name}:")
            parts.append('    """Generated test cases with comprehensive coverage."""')
            parts.append('')
            
            for component in components:
                # Add component test methods
                methods = component.template_code.split('\n')
                for method in methods:
                    if method.strip():
                        parts.append(method)
                parts.append('')
        
        return '\n'.join(parts)
    
    def _calculate_quality_score(self, components: List[TestTemplate], analysis: Dict[str, Any]) -> float:
        """Calculate overall test quality score."""
        if not components:
            return 0.0
        
        base_scores = [comp.quality_score for comp in components]
        base_average = sum(base_scores) / len(base_scores)
        
        # Bonus points for comprehensive coverage
        bonuses = 0.0
        if analysis["business_logic"]["business_value"] != "low":
            bonuses += 5.0
        if analysis["dependencies"]:
            bonuses += 5.0
        if analysis["error_scenarios"]:
            bonuses += 5.0
        
        return min(100.0, base_average + bonuses)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for test improvement."""
        recommendations = []
        
        if analysis["business_logic"]["business_value"] == "low":
            recommendations.append("Consider refactoring function to include more business logic worth testing")
        
        if not analysis["dependencies"]:
            recommendations.append("Function appears self-contained - good for unit testing")
        
        if not analysis["error_scenarios"]:
            recommendations.append("Consider adding error handling for robustness")
        
        if analysis["complexity_score"] > 10:
            recommendations.append("Function is complex - consider breaking into smaller, testable functions")
        
        return recommendations


# CLI Interface
def main():
    """CLI interface for test creation skills."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate high-quality tests using creation skills")
    parser.add_argument("function_file", help="Python file containing the function to test")
    parser.add_argument("--function", help="Specific function name to test")
    parser.add_argument("--context", choices=["mcp_tools", "api_responses", "user_inputs"], 
                       default="mcp_tools", help="Test context for data generation")
    parser.add_argument("--output", help="Output file for generated tests")
    
    args = parser.parse_args()
    
    # Read the function file
    try:
        with open(args.function_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return 1
    
    # Parse the file to extract functions
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ Syntax error in file: {e}")
        return 1
    
    orchestrator = TestSkillOrchestrator()
    context = {"type": args.context}
    
    # Generate tests for specified function or all functions
    if args.function:
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == args.function]
    else:
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    if not functions:
        print(f"❌ No functions found")
        return 1
    
    all_tests = []
    
    for func in functions:
        function_code = ast.get_source_segment(content, func)
        if function_code:
            result = orchestrator.generate_comprehensive_tests(
                func.name, function_code, context
            )
            all_tests.append(result)
            
            print(f"✅ Generated {result['test_components']} test components for {func.name}")
            print(f"📊 Quality score: {result['quality_score']:.1f}%")
            
            if result["recommendations"]:
                print("💡 Recommendations:")
                for rec in result["recommendations"]:
                    print(f"   - {rec}")
            print()
    
    # Write output file if specified
    if args.output and all_tests:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                # Combine all tests
                combined_code = []
                for i, test_result in enumerate(all_tests):
                    if i > 0:
                        combined_code.append("\n" + "="*50 + "\n")
                    combined_code.append(test_result["test_code"])
                
                f.write('\n'.join(combined_code))
            
            print(f"📁 Tests written to: {args.output}")
        except Exception as e:
            print(f"❌ Error writing output file: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())