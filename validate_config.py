#!/usr/bin/env python3
"""
Configuration validation script for MCP Gateway
Validates that all critical configuration fixes are properly applied
"""

import sys
import os
import yaml
from pathlib import Path

def validate_dribbble_config():
    """Validate dribbble-mcp service has required command field"""
    try:
        config_path = Path("config/services.yml")
        if not config_path.exists():
            print("❌ config/services.yml not found")
            return False

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        dribbble = config.get('dribbble-mcp', {})
        if not dribbble:
            print("❌ dribbble-mcp service not found in config")
            return False

        command = dribbble.get('command')
        if not command:
            print("❌ dribbble-mcp missing command field")
            return False

        expected_command = ["python3", "-m", "dribbble_mcp"]
        if command != expected_command:
            print(f"❌ dribbble-mcp command incorrect: {command} != {expected_command}")
            return False

        print("✅ dribbble-mcp configuration valid")
        return True

    except Exception as e:
        print(f"❌ Error validating dribbble config: {e}")
        return False

def validate_forge_context_config():
    """Validate forge-context service is properly configured"""
    try:
        config_path = Path("config/services.yml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        forge_context = config.get('forge-context', {})
        if not forge_context:
            print("❌ forge-context service not found in config")
            return False

        # Check required fields
        required_fields = ['image', 'command', 'port']
        for field in required_fields:
            if field not in forge_context:
                print(f"❌ forge-context missing required field: {field}")
                return False

        # Check high priority configuration
        sleep_policy = forge_context.get('sleep_policy', {})
        if sleep_policy.get('priority') != 'high':
            print("❌ forge-context should have high priority sleep policy")
            return False

        print("✅ forge-context configuration valid")
        return True

    except Exception as e:
        print(f"❌ Error validating forge-context config: {e}")
        return False

def validate_docker_compose_volumes():
    """Validate forge-ui volume mount in docker-compose.yml"""
    try:
        compose_path = Path("docker-compose.yml")
        if not compose_path.exists():
            print("❌ docker-compose.yml not found")
            return False

        with open(compose_path, 'r') as f:
            compose = yaml.safe_load(f)

        services = compose.get('services', {})
        forge_ui = services.get('forge-ui', {})
        if not forge_ui:
            print("❌ forge-ui service not found in docker-compose.yml")
            return False

        volumes = forge_ui.get('volumes', [])
        data_dev_volume = "./data-dev:/data-dev"
        if data_dev_volume not in volumes:
            print(f"❌ forge-ui missing data-dev volume mount: {data_dev_volume}")
            return False

        print("✅ forge-ui volume mount valid")
        return True

    except Exception as e:
        print(f"❌ Error validating docker-compose volumes: {e}")
        return False

def validate_service_manager_fix():
    """Validate service-manager Docker client fix"""
    try:
        service_manager_path = Path("service-manager/service_manager.py")
        if not service_manager_path.exists():
            print("❌ service-manager.py not found")
            return False

        with open(service_manager_path, 'r') as f:
            content = f.read()

        # Check for the fix: DockerClient with explicit socket path
        if 'docker.DockerClient(base_url="unix://var/run/docker.sock")' not in content:
            print("❌ service-manager Docker client fix not applied")
            return False

        # Check that the old from_env() call is not present in initialize method
        if 'docker.from_env()' in content:
            print("❌ service-manager still contains docker.from_env() call")
            return False

        print("✅ service-manager Docker client fix valid")
        return True

    except Exception as e:
        print(f"❌ Error validating service-manager fix: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🔍 Validating MCP Gateway Configuration Fixes...")
    print("=" * 50)

    checks = [
        validate_dribbble_config,
        validate_forge_context_config,
        validate_docker_compose_volumes,
        validate_service_manager_fix
    ]

    results = []
    for check in checks:
        results.append(check())
        print()

    passed = sum(results)
    total = len(results)

    print("=" * 50)
    print(f"📊 Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All configuration fixes validated successfully!")
        return 0
    else:
        print("⚠️  Some configuration issues detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())
