#!/usr/bin/env python3
"""
Register existing UIForge templates in the template registry.

This script discovers and registers existing templates from the config/shared directory
into the template registry with proper metadata and versioning.
"""

import sys
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location("template_registry", "template-registry.py")
template_registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_registry)

TemplateRegistry = template_registry.TemplateRegistry
TemplateInstance = template_registry.TemplateInstance
TemplateMetadata = template_registry.TemplateMetadata
TemplateType = template_registry.TemplateType


def register_existing_templates():
    """Register existing templates from config/shared directory."""
    registry = TemplateRegistry()
    shared_dir = Path("../../config/shared")

    if not shared_dir.exists():
        print(f"Error: {shared_dir} directory not found")
        return 1

    # Template definitions
    templates = [
        {
            "file": shared_dir / "package.json.template",
            "type": TemplateType.PACKAGE_JSON,
            "name": "uiforge-package",
            "version": "1.0.0",
            "description": "UIForge Node.js package template with MCP SDK and standard scripts",
            "tags": ["nodejs", "package", "mcp", "uiforge"],
            "variables": ["project-name", "project-description", "project-repo"],
            "compatibility": {"node": ">=18.0.0"}
        },
        {
            "file": shared_dir / "pyproject.toml.template",
            "type": TemplateType.PYPROJECT_TOML,
            "name": "uiforge-python",
            "version": "1.0.0",
            "description": "UIForge Python project template with FastAPI and comprehensive tooling",
            "tags": ["python", "fastapi", "pyproject", "uiforge"],
            "variables": ["project-name", "project-description", "project-repo", "package_name"],
            "compatibility": {"python": ">=3.11"}
        },
        {
            "file": shared_dir / "tsconfig.json.template",
            "type": TemplateType.TSCONFIG_JSON,
            "name": "uiforge-typescript",
            "version": "1.0.0",
            "description": "UIForge TypeScript configuration with strict mode and path mappings",
            "tags": ["typescript", "tsconfig", "uiforge"],
            "variables": [],
            "compatibility": {"node": ">=18.0.0"}
        }
    ]

    registered_count = 0

    for template_def in templates:
        template_file = template_def["file"]

        if not template_file.exists():
            print(f"Warning: Template file {template_file} not found, skipping")
            continue

        # Read template content
        with open(template_file, 'r') as f:
            content = f.read()

        # Create metadata
        metadata = TemplateMetadata(
            name=template_def["name"],
            type=template_def["type"],
            version=template_def["version"],
            description=template_def["description"],
            tags=template_def["tags"],
            variables=template_def["variables"],
            compatibility=template_def["compatibility"]
        )

        # Create template instance
        instance = TemplateInstance(
            metadata=metadata,
            content=content,
            file_path=str(template_file)
        )

        try:
            # Register template
            template_id = registry.register_template(instance)
            print(f"✅ Registered template: {template_id}")
            registered_count += 1
        except ValueError as e:
            print(f"❌ Failed to register {template_def['name']}: {e}")

    print(f"\n📊 Summary: Registered {registered_count} templates")
    return 0


def main():
    """Main entry point."""
    return register_existing_templates()


if __name__ == "__main__":
    sys.exit(main())
