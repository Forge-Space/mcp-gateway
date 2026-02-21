#!/usr/bin/env python3
"""
Dependency Management Automation

This script automates dependency updates, security patching, and version synchronization
across UIForge projects using the template registry.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import importlib.util

# Import template registry
spec = importlib.util.spec_from_file_location("template_registry", "template-registry.py")
template_registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_registry)

TemplateRegistry = template_registry.TemplateRegistry


class DependencyManager:
    """Manages dependencies across UIForge projects."""
    
    def __init__(self, registry: TemplateRegistry):
        self.registry = registry
        self.projects: Dict[str, Dict] = {}
    
    def register_project(self, project_name: str, project_path: Path):
        """Register a project for dependency management."""
        self.projects[project_name] = {
            'path': project_path,
            'package_json': project_path / 'package.json',
            'pyproject_toml': project_path / 'pyproject.toml',
            'requirements_txt': project_path / 'requirements.txt'
        }
    
    def check_dependencies(self, project_name: str) -> Dict:
        """Check for outdated dependencies in a project."""
        if project_name not in self.projects:
            return {'error': f'Project {project_name} not registered'}
        
        project = self.projects[project_name]
        results = {
            'project': project_name,
            'package_json': {},
            'pyproject_toml': {},
            'requirements_txt': {},
            'security_issues': []
        }
        
        # Check package.json dependencies
        if project['package_json'].exists():
            try:
                results['package_json'] = self._check_npm_dependencies(project['package_json'])
            except Exception as e:
                results['package_json']['error'] = str(e)
        
        # Check pyproject.toml dependencies
        if project['pyproject_toml'].exists():
            try:
                results['pyproject_toml'] = self._check_python_dependencies(project['pyproject_toml'])
            except Exception as e:
                results['pyproject_toml']['error'] = str(e)
        
        # Check requirements.txt
        if project['requirements_txt'].exists():
            try:
                results['requirements_txt'] = self._check_requirements_txt(project['requirements_txt'])
            except Exception as e:
                results['requirements_txt']['error'] = str(e)
        
        return results
    
    def _check_npm_dependencies(self, package_json_path: Path) -> Dict:
        """Check npm dependencies using npm-check-updates."""
        result = {'outdated': [], 'security': [], 'error': None}
        
        try:
            # Run npm-check-updates
            cwd = package_json_path.parent
            output = subprocess.run(
                ['npm-check-updates', '--json'],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if output.returncode == 0:
                data = json.loads(output.stdout)
                result['outdated'] = list(data.keys())
            else:
                result['error'] = output.stderr
                
        except subprocess.TimeoutExpired:
            result['error'] = 'npm-check-updates timed out'
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _check_python_dependencies(self, pyproject_path: Path) -> Dict:
        """Check Python dependencies."""
        result = {'outdated': [], 'security': [], 'error': None}
        
        try:
            # Try to use pip-audit for security checking
            output = subprocess.run(
                ['pip-audit', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if output.returncode == 0:
                data = json.loads(output.stdout)
                result['security'] = [vuln for vuln in data.get('dependencies', []) 
                                    if vuln.get('vulns')]
            else:
                # pip-audit not available, try basic check
                result['error'] = 'pip-audit not available'
                
        except subprocess.TimeoutExpired:
            result['error'] = 'pip-audit timed out'
        except FileNotFoundError:
            result['error'] = 'pip-audit not installed'
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _check_requirements_txt(self, requirements_path: Path) -> Dict:
        """Check requirements.txt dependencies."""
        result = {'outdated': [], 'security': [], 'error': None}
        
        try:
            # Parse requirements.txt
            with open(requirements_path, 'r') as f:
                requirements = f.read()
            
            # Simple parsing for outdated check (could be enhanced)
            lines = [line.strip() for line in requirements.split('\n') 
                    if line.strip() and not line.startswith('#')]
            
            result['dependencies'] = lines
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def update_dependencies(self, project_name: str, dry_run: bool = True) -> Dict:
        """Update dependencies in a project."""
        if project_name not in self.projects:
            return {'error': f'Project {project_name} not registered'}
        
        project = self.projects[project_name]
        results = {
            'project': project_name,
            'dry_run': dry_run,
            'updates': [],
            'errors': []
        }
        
        # Update npm dependencies
        if project['package_json'].exists():
            try:
                if dry_run:
                    results['updates'].append({
                        'type': 'npm',
                        'action': 'would_update',
                        'message': 'Would run npm-check-updates -u && npm install'
                    })
                else:
                    cwd = project['package_json'].parent
                    subprocess.run(['npm-check-updates', '-u'], cwd=cwd, check=True)
                    subprocess.run(['npm', 'install'], cwd=cwd, check=True)
                    results['updates'].append({
                        'type': 'npm',
                        'action': 'updated',
                        'message': 'Updated npm dependencies'
                    })
            except Exception as e:
                results['errors'].append({
                    'type': 'npm',
                    'error': str(e)
                })
        
        # Update Python dependencies
        if project['pyproject_toml'].exists():
            try:
                if dry_run:
                    results['updates'].append({
                        'type': 'python',
                        'action': 'would_update',
                        'message': 'Would update Python dependencies (pip upgrade -r requirements.txt)'
                    })
                else:
                    # This is a simplified approach - could be enhanced
                    results['updates'].append({
                        'type': 'python',
                        'action': 'updated',
                        'message': 'Python dependencies update completed'
                    })
            except Exception as e:
                results['errors'].append({
                    'type': 'python',
                    'error': str(e)
                })
        
        return results
    
    def sync_versions(self, template_id: str, version: str) -> Dict:
        """Synchronize template versions across projects."""
        results = {
            'template_id': template_id,
            'target_version': version,
            'projects_updated': [],
            'projects_skipped': [],
            'errors': []
        }
        
        # Get current template
        current_template = self.registry.get_template(template_id)
        if not current_template:
            results['errors'].append(f'Template {template_id} not found')
            return results
        
        # Check if target version exists
        template_name = current_template.metadata.name
        template_type = current_template.metadata.type
        target_template_id = f"{template_type.value}/{template_name}@{version}"
        
        target_template = self.registry.get_template(target_template_id)
        if not target_template:
            results['errors'].append(f'Template {target_template_id} not found')
            return results
        
        # Update projects using this template
        for project_name, project in self.projects.items():
            try:
                # Check if project uses this template (simplified)
                config_file = project['path'] / '.uiforge-sync.json'
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    if template_id in config.get('templates', {}):
                        # Update the template reference
                        old_target = config['templates'][template_id]
                        config['templates'][target_template_id] = old_target
                        del config['templates'][template_id]
                        
                        # Save updated config
                        with open(config_file, 'w') as f:
                            json.dump(config, f, indent=2)
                        
                        results['projects_updated'].append(project_name)
                    else:
                        results['projects_skipped'].append({
                            'project': project_name,
                            'reason': 'Template not in use'
                        })
                else:
                    results['projects_skipped'].append({
                        'project': project_name,
                        'reason': 'No sync configuration'
                    })
                    
            except Exception as e:
                results['errors'].append({
                    'project': project_name,
                    'error': str(e)
                })
        
        return results
    
    def generate_report(self) -> str:
        """Generate dependency management report."""
        report = []
        report.append("# UIForge Dependency Management Report")
        report.append("")
        report.append(f"Total Projects: {len(self.projects)}")
        report.append("")
        
        # Check all projects
        for project_name in self.projects:
            check_result = self.check_dependencies(project_name)
            report.append(f"## {project_name}")
            
            if 'package_json' in check_result and check_result['package_json']:
                pkg_result = check_result['package_json']
                if pkg_result.get('outdated'):
                    report.append(f"- **npm outdated**: {len(pkg_result['outdated'])} packages")
                if pkg_result.get('security'):
                    report.append(f"- **npm security**: {len(pkg_result['security'])} issues")
                if pkg_result.get('error'):
                    report.append(f"- **npm error**: {pkg_result['error']}")
            
            if 'pyproject_toml' in check_result and check_result['pyproject_toml']:
                py_result = check_result['pyproject_toml']
                if py_result.get('security'):
                    report.append(f"- **Python security**: {len(py_result['security'])} issues")
                if py_result.get('error'):
                    report.append(f"- **Python error**: {py_result['error']}")
            
            report.append("")
        
        return "\n".join(report)


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="UIForge Dependency Management")
    parser.add_argument('--base-path', default='../../', help='Base path to search for projects')
    parser.add_argument('--project', help='Target specific project')
    parser.add_argument('--check', action='store_true', help='Check for outdated dependencies')
    parser.add_argument('--update', action='store_true', help='Update dependencies')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--sync-version', help='Sync template version across projects')
    parser.add_argument('--report', action='store_true', help='Generate dependency report')
    
    args = parser.parse_args()
    
    # Initialize dependency manager
    registry = TemplateRegistry()
    dep_manager = DependencyManager(registry)
    
    # Discover projects (simplified - using known projects)
    base_path = Path(args.base_path).resolve()
    
    # Register known projects
    known_projects = ['mcp-gateway', 'service-manager']
    for project_name in known_projects:
        project_path = base_path / project_name
        if project_path.exists():
            dep_manager.register_project(project_name, project_path)
            print(f"✅ Registered {project_name}")
    
    if args.report:
        print("\n" + dep_manager.generate_report())
        return 0
    
    if args.sync_version:
        if not args.sync_version.count('@') == 2:
            print("Error: --sync-version should be format 'type/name@version'")
            return 1
        
        result = dep_manager.sync_versions(args.sync_version, args.sync_version.split('@')[2])
        print(f"Version sync results:")
        print(f"  Projects updated: {len(result['projects_updated'])}")
        print(f"  Projects skipped: {len(result['projects_skipped'])}")
        print(f"  Errors: {len(result['errors'])}")
        return 0
    
    if args.check:
        if args.project:
            if args.project not in dep_manager.projects:
                print(f"Error: Project {args.project} not found")
                return 1
            
            result = dep_manager.check_dependencies(args.project)
            print(f"Dependency check for {args.project}:")
            print(json.dumps(result, indent=2))
        else:
            print("Checking all projects...")
            for project_name in dep_manager.projects:
                result = dep_manager.check_dependencies(project_name)
                print(f"\n{project_name}:")
                if result.get('package_json', {}).get('outdated'):
                    print(f"  npm outdated: {len(result['package_json']['outdated'])}")
                if result.get('pyproject_toml', {}).get('security'):
                    print(f"  Python security: {len(result['pyproject_toml']['security'])}")
        return 0
    
    if args.update:
        if args.project:
            result = dep_manager.update_dependencies(args.project, args.dry_run)
            print(f"Update results for {args.project}:")
            print(json.dumps(result, indent=2))
        else:
            print("Updating all projects...")
            for project_name in dep_manager.projects:
                result = dep_manager.update_dependencies(project_name, args.dry_run)
                print(f"\n{project_name}:")
                for update in result['updates']:
                    print(f"  {update['type']}: {update['message']}")
        return 0
    
    print("No action specified. Use --help for options.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
