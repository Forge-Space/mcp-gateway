#!/usr/bin/env python3
"""
Ollama Service Diagnostics Script

This script helps diagnose ollama service issues in the MCP Gateway.
Run this script to check ollama configuration and connectivity.
"""

import requests
import subprocess
import sys
import time
from pathlib import Path


def check_docker_running():
    """Check if Docker is running"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_ollama_container():
    """Check if ollama container is running"""
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=forge-ollama', 
                                  '--format', '{{.Status}}'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return True, result.stdout.strip()
        return False, "Container not found"
    except Exception as e:
        return False, f"Error checking container: {e}"


def check_ollama_service():
    """Check if ollama service is responding"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return False


def check_ollama_models():
    """Check if ollama has models available"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            return len(models) > 0, models
        return False, []
    except Exception:
        return False, []


def check_env_config():
    """Check environment configuration"""
    env_file = Path('.env')
    if not env_file.exists():
        return False, ".env file not found"
    
    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value
    
    issues = []
    
    # Check AI routing settings
    if config.get('ROUTER_AI_ENABLED') == 'false':
        issues.append("ROUTER_AI_ENABLED is set to false")
    
    if not config.get('OLLAMA_PORT'):
        issues.append("OLLAMA_PORT not set")
    
    if config.get('ROUTER_AI_PROVIDER') != 'ollama':
        issues.append("ROUTER_AI_PROVIDER is not set to ollama")
    
    return len(issues) == 0, issues


def main():
    """Main diagnostic function"""
    print("🔍 Ollama Service Diagnostics")
    print("=" * 40)
    
    # Check Docker
    print("\n1. Docker Status:")
    docker_running = check_docker_running()
    if docker_running:
        print("   ✅ Docker is running")
    else:
        print("   ❌ Docker is not running")
        print("   💡 Start Docker Desktop to continue")
        return 1
    
    # Check ollama container
    print("\n2. Ollama Container Status:")
    container_running, container_status = check_ollama_container()
    if container_running:
        print(f"   ✅ Ollama container is running: {container_status}")
    else:
        print(f"   ❌ Ollama container issue: {container_status}")
        print("   💡 Run: docker-compose up ollama")
        return 1
    
    # Check ollama service
    print("\n3. Ollama Service Connectivity:")
    service_running = check_ollama_service()
    if service_running:
        print("   ✅ Ollama API is responding")
    else:
        print("   ❌ Ollama API is not responding")
        print("   💡 Check container logs: docker logs forge-ollama")
        return 1
    
    # Check models
    print("\n4. Ollama Models:")
    has_models, models = check_ollama_models()
    if has_models:
        print(f"   ✅ Found {len(models)} model(s):")
        for model in models[:3]:  # Show first 3 models
            print(f"      - {model.get('name', 'Unknown')}")
        if len(models) > 3:
            print(f"      ... and {len(models) - 3} more")
    else:
        print("   ❌ No models found")
        print("   💡 Pull a model: docker exec forge-ollama ollama pull llama3.2:3b")
        return 1
    
    # Check configuration
    print("\n5. Environment Configuration:")
    config_ok, issues = check_env_config()
    if config_ok:
        print("   ✅ Environment configuration looks good")
    else:
        print("   ⚠️ Configuration issues found:")
        for issue in issues:
            print(f"      - {issue}")
    
    print("\n" + "=" * 40)
    if docker_running and container_running and service_running and has_models:
        print("🎉 Ollama service is healthy!")
        if not config_ok:
            print("⚠️ Consider fixing configuration issues for optimal performance")
        return 0
    else:
        print("❌ Ollama service needs attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
