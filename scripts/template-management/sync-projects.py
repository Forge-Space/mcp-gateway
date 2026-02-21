#!/usr/bin/env python3
"""
Cross-Project Template Synchronization

This script synchronizes templates across multiple UIForge projects using the template registry.
It supports bulk operations, conflict detection, and progress tracking.
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import importlib.util

# Import template registry
spec = importlib.util.spec_from_file_location("template_registry", "template-registry.py")
template_registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_registry)

TemplateRegistry = template_registry.TemplateRegistry
TemplateInstance = template_registry.TemplateInstance
TemplateMetadata = template_registry.TemplateMetadata
TemplateType = template_registry.TemplateType


class ProjectSyncManager:
    """Manages synchronization across multiple UIForge projects."""

    def __init__(self, registry: TemplateRegistry):
        self.registry = registry
        self.projects: Dict[str, Dict] = {}
        self.sync_results: Dict[str, List[Dict]] = {}

    def discover_projects(self, base_path: Path) -> List[str]:
        """Discover UIForge projects in the given base path."""
        projects = []

        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if this looks like a UIForge project
                if self._is_uiforge_project(item):
                    projects.append(item.name)

        return sorted(projects)

    def _is_uiforge_project(self, path: Path) -> bool:
        """Check if a directory is a UIForge project."""
        indicators = [
            "package.json",
            "pyproject.toml",
            "tsconfig.json",
            ".env.shared",
            "config/shared"
        ]

        return any((path / indicator).exists() for indicator in indicators)

    def register_project(self, project_name: str, project_path: Path, config: Dict):
        """Register a project for synchronization."""
        self.projects[project_name] = {
            'path': project_path,
            'config': config,
            'last_sync': None,
            'status': 'registered'
        }

    def sync_project(self, project_name: str, dry_run: bool = False) -> Dict:
        """Synchronize a single project with templates."""
        if project_name not in self.projects:
            return {'success': False, 'error': f'Project {project_name} not registered'}

        project = self.projects[project_name]
        project_path = project['path']
        config = project['config']

        results = {
            'project': project_name,
            'dry_run': dry_run,
            'templates_updated': [],
            'templates_skipped': [],
            'errors': [],
            'warnings': []
        }

        # Get project variables
        variables = config.get('variables', {})

        # Sync each template type
        template_mappings = config.get('templates', {})

        for template_id, target_file in template_mappings.items():
            try:
                result = self._sync_template(template_id, project_path / target_file, variables, dry_run)
                result['template_id'] = template_id
                result['target_file'] = target_file

                if result['success']:
                    if result['updated']:
                        results['templates_updated'].append(result)
                    else:
                        results['templates_skipped'].append(result)
                else:
                    results['errors'].append(result)

            except Exception as e:
                results['errors'].append({
                    'template_id': template_id,
                    'target_file': target_file,
                    'error': str(e)
                })

        # Update project status
        if not dry_run and not results['errors']:
            project['last_sync'] = template_registry.datetime.datetime.now().isoformat()
            project['status'] = 'synced'

        return results

    def _sync_template(self, template_id: str, target_file: Path, variables: Dict, dry_run: bool) -> Dict:
        """Sync a single template to a target file."""
        result = {
            'success': False,
            'updated': False,
            'checksum_match': False,
            'error': None
        }

        # Get template from registry
        instance = self.registry.get_template(template_id)
        if not instance:
            result['error'] = f'Template {template_id} not found in registry'
            return result

        # Generate content with variables
        try:
            content = self.registry.create_template_instance(template_id, variables)
        except Exception as e:
            result['error'] = f'Failed to generate template content: {e}'
            return result

        # Check if target file exists
        if target_file.exists():
            # Read existing content
            with open(target_file, 'r') as f:
                existing_content = f.read()

            # Check if content is the same
            if content == existing_content:
                result['success'] = True
                result['updated'] = False
                result['checksum_match'] = True
                return result

            # Check if only version/author changed (preserve customizations)
            if self._is_version_only_change(existing_content, content):
                result['success'] = True
                result['updated'] = True
                result['version_update'] = True
        else:
            result['success'] = True
            result['updated'] = True
            result['new_file'] = True

        # Write file if not dry run
        if not dry_run and result['success'] and result['updated']:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w') as f:
                f.write(content)

        return result

    def _is_version_only_change(self, existing: str, new: str) -> bool:
        """Check if the change is only in version/author metadata."""
        try:
            if existing.strip().startswith('{') and new.strip().startswith('{'):
                existing_json = json.loads(existing)
                new_json = json.loads(new)

                # Copy non-metadata fields from new to existing
                for key, value in new_json.items():
                    if key not in ['version', 'author', 'description']:
                        if key not in existing_json or existing_json[key] != value:
                            return False

                return True
        except json.JSONDecodeError:
            pass

        return False

    def sync_all_projects(self, dry_run: bool = False) -> Dict:
        """Synchronize all registered projects."""
        results = {
            'total_projects': len(self.projects),
            'successful_syncs': 0,
            'failed_syncs': 0,
            'projects': {}
        }

        for project_name in self.projects:
            project_result = self.sync_project(project_name, dry_run)
            results['projects'][project_name] = project_result

            if project_result['errors']:
                results['failed_syncs'] += 1
            else:
                results['successful_syncs'] += 1

        return results

    def detect_conflicts(self) -> Dict:
        """Detect potential conflicts across projects."""
        conflicts = {
            'version_mismatches': [],
            'missing_variables': [],
            'template_mismatches': []
        }

        # Check for version mismatches
        template_versions = {}
        for project_name, project in self.projects.items():
            templates = project['config'].get('templates', {})
            for template_id in templates:
                if template_id not in template_versions:
                    template_versions[template_id] = []
                template_versions[template_id].append(project_name)

        # Check if projects are using different versions of the same template
        for template_id, projects_list in template_versions.items():
            if len(projects_list) > 1:
                # Extract template name and version
                if '@' in template_id:
                    template_name, version = template_id.rsplit('@', 1)
                    same_name_projects = [p for p in self.projects.keys()
                                        if any(t.startswith(f"{template_name}@") for t in self.projects[p]['config'].get('templates', {}))]
                    if len(same_name_projects) > 1:
                        conflicts['version_mismatches'].append({
                            'template_name': template_name,
                            'projects': same_name_projects,
                            'template_ids': [t for p in same_name_projects
                                           for t in self.projects[p]['config'].get('templates', {})
                                           if t.startswith(f"{template_name}@")]
                        })

        return conflicts

    def generate_report(self) -> str:
        """Generate a synchronization report."""
        report = []
        report.append("# UIForge Cross-Project Synchronization Report")
        report.append("")
        report.append(f"Total Projects: {len(self.projects)}")
        report.append("")

        # Project status
        report.append("## Project Status")
        for project_name, project in self.projects.items():
            status = project['status']
            last_sync = project.get('last_sync', 'Never')
            report.append(f"- **{project_name}**: {status} (Last sync: {last_sync})")

        report.append("")

        # Conflicts
        conflicts = self.detect_conflicts()
        if any(conflicts.values()):
            report.append("## Detected Conflicts")
            if conflicts['version_mismatches']:
                report.append("### Version Mismatches")
                for mismatch in conflicts['version_mismatches']:
                    report.append(f"- {mismatch['template_name']}: {', '.join(mismatch['projects'])}")
            report.append("")

        return "\n".join(report)


def load_project_config(project_path: Path) -> Optional[Dict]:
    """Load project configuration from .uiforge-sync.json or similar."""
    # Ensure the project path is within expected bounds
    try:
        project_path = project_path.resolve()
        # Additional safety check: ensure we're not going outside expected directories
        if not str(project_path).startswith('/Users/lucassantana/Desenvolvimento'):
            print(f"Warning: Project path {project_path} outside expected directory")
            return None
    except (OSError, ValueError) as e:
        print(f"Error resolving project path {project_path}: {e}")
        return None

    config_file = project_path / ".uiforge-sync.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error reading config file {config_file}: {e}")
            return None

    # Try to infer configuration
    config = {
        'variables': {},
        'templates': {}
    }

    # Infer variables from project name
    project_name = project_path.name
    config['variables'] = {
        'project-name': project_name,
        'project-description': f'UIForge {project_name} project',
        'project-repo': project_name,
        'package_name': project_name.replace('-', '_')
    }

    # Infer template mappings
    if (project_path / "package.json").exists():
        config['templates']['package.json/uiforge-package@1.0.0'] = "package.json"

    if (project_path / "pyproject.toml").exists():
        config['templates']['pyproject.toml/uiforge-python@1.0.0'] = "pyproject.toml"

    if (project_path / "tsconfig.json").exists():
        config['templates']['tsconfig.json/uiforge-typescript@1.0.0'] = "tsconfig.json"

    return config if config['templates'] else None


def validate_path_safe(path_str: str) -> bool:
    """Validate that a path string is safe and doesn't contain traversal attempts."""
    # Check for path traversal attempts
    dangerous_patterns = ['..', '~/', '/etc/', '/var/', '/usr/', '/bin/', '/sbin/']
    path_str = path_str.strip()

    for pattern in dangerous_patterns:
        if pattern in path_str:
            return False

    # Ensure path doesn't start with slash (absolute path)
    if path_str.startswith('/'):
        return False

    return True


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="UIForge Cross-Project Synchronization")
    parser.add_argument('--base-path', default='../../', help='Base path to search for projects')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--project', help='Sync specific project only')
    parser.add_argument('--report', action='store_true', help='Generate synchronization report')

    args = parser.parse_args()

    # Validate input parameters for security
    if not validate_path_safe(args.base_path):
        print("Error: Invalid base path detected")
        return 1

    if args.project and not validate_path_safe(args.project):
        print("Error: Invalid project name detected")
        return 1

    # Initialize registry and sync manager
    registry = TemplateRegistry()
    sync_manager = ProjectSyncManager(registry)

    # Discover projects
    base_path = Path(args.base_path).resolve()
    projects = sync_manager.discover_projects(base_path)

    print(f"Discovered {len(projects)} UIForge projects:")
    for project in projects:
        print(f"  - {project}")

    # Register projects
    for project_name in projects:
        project_path = base_path / project_name
        config = load_project_config(project_path)

        if config:
            sync_manager.register_project(project_name, project_path, config)
            print(f"✅ Registered {project_name}")
        else:
            print(f"⚠️  Skipped {project_name} (no configuration)")

    if args.report:
        print("\n" + sync_manager.generate_report())
        return 0

    # Sync projects
    if args.project:
        if args.project not in sync_manager.projects:
            print(f"Error: Project {args.project} not found")
            return 1

        print(f"\n🔄 Syncing project: {args.project}")
        result = sync_manager.sync_project(args.project, args.dry_run)
        print(f"Templates updated: {len(result['templates_updated'])}")
        print(f"Templates skipped: {len(result['templates_skipped'])}")
        print(f"Errors: {len(result['errors'])}")

        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")
    else:
        print(f"\n🔄 Syncing all projects ({'DRY RUN' if args.dry_run else 'LIVE'})")
        results = sync_manager.sync_all_projects(args.dry_run)

        print(f"Successful syncs: {results['successful_syncs']}")
        print(f"Failed syncs: {results['failed_syncs']}")

        for project_name, result in results['projects'].items():
            if result['errors']:
                print(f"\n❌ {project_name} had errors:")
                for error in result['errors']:
                    print(f"  - {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
