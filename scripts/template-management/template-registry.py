#!/usr/bin/env python3
"""
UIForge Template Registry - Template Management System

This module provides a comprehensive template management system with:
- Template versioning (semantic versioning)
- Template registry and catalog
- Template inheritance framework
- Version compatibility checking
- Template validation and testing
"""

import json
import semver
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class TemplateType(Enum):
    """Template types supported by the registry."""
    PACKAGE_JSON = "package.json"
    PYPROJECT_TOML = "pyproject.toml"
    TSCONFIG_JSON = "tsconfig.json"
    DOCKERFILE = "Dockerfile"
    GITHUB_ACTIONS = "github-actions"
    ESLINT_CONFIG = "eslint.config.js"


@dataclass
class TemplateMetadata:
    """Metadata for a template."""
    name: str
    type: TemplateType
    version: str
    description: str
    author: str = "UIForge Contributors"
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = None
    dependencies: List[str] = None
    compatibility: Dict[str, str] = None
    variables: List[str] = None
    base_template: Optional[str] = None
    checksum: str = ""

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.datetime.now().isoformat()
        if self.updated_at == "":
            self.updated_at = self.created_at
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
        if self.compatibility is None:
            self.compatibility = {}
        if self.variables is None:
            self.variables = []


@dataclass
class TemplateInstance:
    """A specific instance of a template."""
    metadata: TemplateMetadata
    content: str
    file_path: str

    def calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of template content."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate template content and metadata."""
        errors = []

        # Validate version format
        try:
            semver.VersionInfo.parse(self.metadata.version)
        except ValueError:
            errors.append(f"Invalid semantic version: {self.metadata.version}")

        # Validate checksum
        expected_checksum = self.calculate_checksum()
        if self.metadata.checksum != expected_checksum:
            errors.append(f"Checksum mismatch: expected {expected_checksum}, got {self.metadata.checksum}")

        # Validate template type specific content
        if self.metadata.type == TemplateType.PACKAGE_JSON:
            try:
                json.loads(self.content)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in package.json template: {e}")

        # Validate required variables
        for variable in self.metadata.variables:
            if f"{{{variable}}}" not in self.content:
                errors.append(f"Variable {variable} not found in template content")

        return len(errors) == 0, errors


class TemplateRegistry:
    """Central template registry for UIForge projects."""

    def __init__(self, registry_path: Optional[Path] = None):
        if registry_path is None:
            # Try to find the registry relative to the script location
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            self.registry_path = project_root / "config/template-registry"
        else:
            self.registry_path = registry_path
        self.templates: Dict[str, TemplateInstance] = {}
        self.load_registry()

    def load_registry(self):
        """Load template registry from disk."""
        registry_file = self.registry_path / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    for template_id, template_data in data.items():
                        metadata_dict = template_data['metadata']
                        # Convert string back to TemplateType enum
                        metadata_dict['type'] = TemplateType(metadata_dict['type'])
                        metadata = TemplateMetadata(**metadata_dict)
                        instance = TemplateInstance(
                            metadata=metadata,
                            content=template_data['content'],
                            file_path=template_data['file_path']
                        )
                        self.templates[template_id] = instance
            except Exception as e:
                print(f"Warning: Failed to load registry: {e}")

    def save_registry(self):
        """Save template registry to disk."""
        self.registry_path.mkdir(parents=True, exist_ok=True)
        registry_file = self.registry_path / "registry.json"

        data = {}
        for template_id, instance in self.templates.items():
            metadata_dict = asdict(instance.metadata)
            metadata_dict['type'] = instance.metadata.type.value
            data[template_id] = {
                'metadata': metadata_dict,
                'content': instance.content,
                'file_path': instance.file_path
            }

        with open(registry_file, 'w') as f:
            json.dump(data, f, indent=2)

    def register_template(self, instance: TemplateInstance) -> str:
        """Register a new template in the registry."""
        # Calculate and set checksum
        instance.metadata.checksum = instance.calculate_checksum()

        # Validate template
        is_valid, errors = instance.validate()
        if not is_valid:
            raise ValueError(f"Template validation failed: {errors}")

        # Generate template ID
        template_id = f"{instance.metadata.type.value}/{instance.metadata.name}@{instance.metadata.version}"

        # Check for conflicts
        if template_id in self.templates:
            existing = self.templates[template_id]
            if existing.metadata.checksum == instance.metadata.checksum:
                return template_id  # Same template, no update needed
            else:
                raise ValueError(f"Template {template_id} already exists with different content")

        # Register template
        self.templates[template_id] = instance
        self.save_registry()

        return template_id

    def get_template(self, template_id: str) -> Optional[TemplateInstance]:
        """Get a template by ID."""
        return self.templates.get(template_id)

    def list_templates(self, template_type: Optional[TemplateType] = None) -> List[str]:
        """List all registered templates, optionally filtered by type."""
        templates = list(self.templates.keys())

        if template_type:
            templates = [t for t in templates if t.startswith(template_type.value)]

        return sorted(templates)

    def search_templates(self, query: str) -> List[str]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for template_id, instance in self.templates.items():
            metadata = instance.metadata

            # Search in name, description, and tags
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                results.append(template_id)

        return results

    def get_template_versions(self, template_name: str, template_type: TemplateType) -> List[str]:
        """Get all versions of a specific template."""
        prefix = f"{template_type.value}/{template_name}@"
        versions = []

        for template_id in self.templates:
            if template_id.startswith(prefix):
                version = template_id[len(prefix):]
                versions.append(version)

        return sorted(versions, key=semver.VersionInfo.parse, reverse=True)

    def get_latest_version(self, template_name: str, template_type: TemplateType) -> Optional[str]:
        """Get the latest version of a template."""
        versions = self.get_template_versions(template_name, template_type)
        return versions[0] if versions else None

    def check_compatibility(self, template_id: str, target_version: str) -> Tuple[bool, List[str]]:
        """Check if a template is compatible with a target version."""
        instance = self.get_template(template_id)
        if not instance:
            return False, [f"Template {template_id} not found"]

        metadata = instance.metadata
        issues = []

        # Check Node.js compatibility
        if 'node' in metadata.compatibility:
            required_node = metadata.compatibility['node']
            # Simple version check - could be enhanced with proper semver comparison
            if not target_version.startswith(required_node.replace('>=', '')):
                issues.append(f"Node.js version {target_version} may not be compatible with requirement {required_node}")

        # Check Python compatibility
        if 'python' in metadata.compatibility:
            required_python = metadata.compatibility['python']
            if not target_version.startswith(required_python.replace('>=', '')):
                issues.append(f"Python version {target_version} may not be compatible with requirement {required_python}")

        return len(issues) == 0, issues

    def create_template_instance(self, template_id: str, variables: Dict[str, str]) -> str:
        """Create a template instance with variable substitution."""
        instance = self.get_template(template_id)
        if not instance:
            raise ValueError(f"Template {template_id} not found")

        content = instance.content

        # Substitute variables
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in content:
                content = content.replace(placeholder, var_value)
            else:
                print(f"Warning: Variable {var_name} not found in template")

        return content

    def validate_template_chain(self, template_id: str) -> Tuple[bool, List[str]]:
        """Validate a template and its inheritance chain."""
        errors = []
        visited = set()

        def validate_chain(current_id: str):
            if current_id in visited:
                errors.append(f"Circular dependency detected: {current_id}")
                return

            visited.add(current_id)
            instance = self.get_template(current_id)
            if not instance:
                errors.append(f"Template {current_id} not found")
                return

            # Validate current template
            is_valid, template_errors = instance.validate()
            if not is_valid:
                errors.extend([f"{current_id}: {error}" for error in template_errors])

            # Validate base template if exists
            if instance.metadata.base_template:
                validate_chain(instance.metadata.base_template)

        validate_chain(template_id)
        return len(errors) == 0, errors


def main():
    """CLI entry point for template registry."""
    import argparse

    parser = argparse.ArgumentParser(description="UIForge Template Registry CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List templates')
    list_parser.add_argument('--type', choices=[t.value for t in TemplateType], help='Filter by type')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search templates')
    search_parser.add_argument('query', help='Search query')

    # Info command
    info_parser = subparsers.add_parser('info', help='Get template information')
    info_parser.add_argument('template_id', help='Template ID')

    args = parser.parse_args()

    registry = TemplateRegistry()

    if args.command == 'list':
        template_type = TemplateType(args.type) if args.type else None
        templates = registry.list_templates(template_type)
        for template in templates:
            print(template)

    elif args.command == 'search':
        results = registry.search_templates(args.query)
        for result in results:
            print(result)

    elif args.command == 'info':
        instance = registry.get_template(args.template_id)
        if instance:
            print(f"Template: {instance.metadata.name}")
            print(f"Version: {instance.metadata.version}")
            print(f"Type: {instance.metadata.type.value}")
            print(f"Description: {instance.metadata.description}")
            print(f"Author: {instance.metadata.author}")
            print(f"Created: {instance.metadata.created_at}")
            print(f"Tags: {', '.join(instance.metadata.tags)}")
            if instance.metadata.variables:
                print(f"Variables: {', '.join(instance.metadata.variables)}")
        else:
            print(f"Template {args.template_id} not found")


if __name__ == "__main__":
    main()
