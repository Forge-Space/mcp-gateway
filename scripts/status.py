#!/usr/bin/env python3
"""
Comprehensive System Status for MCP Gateway

Phase 3: Command Simplification
Provides a unified view of system status, services, and configurations.
"""

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class SystemStatus:
    """Comprehensive system status checker."""

    def __init__(self, detailed: bool = False):
        self.repo_root = Path(__file__).parent.parent
        self.detailed = detailed
        self.status = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "unknown",
            "services": {},
            "configurations": {},
            "ide_status": {},
            "docker_status": {},
            "gateway_status": {},
            "recommendations": [],
        }

    def check_docker_status(self) -> dict:
        """Check Docker and Docker Compose status."""
        status = {"docker": "unknown", "compose": "unknown", "containers": {}}

        try:
            # Check Docker daemon
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status["docker"] = "running"
                status["docker_version"] = result.stdout.strip()
            else:
                status["docker"] = "stopped"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            status["docker"] = "not_installed"

        try:
            # Check Docker Compose
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status["compose"] = "available"
                status["compose_version"] = result.stdout.strip()
            else:
                status["compose"] = "not_available"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            status["compose"] = "not_installed"

        # Check container status if Docker is running
        if status["docker"] == "running":
            try:
                result = subprocess.run(
                    ["docker", "ps", "--format", "json"], capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    containers = json.loads(result.stdout)
                    for container in containers:
                        status["containers"][container["Names"]] = {
                            "status": container["Status"],
                            "state": container["State"],
                            "ports": container.get("Ports", []),
                            "image": container["Image"],
                        }
            except (subprocess.TimeoutExpired, json.JSONDecodeError):
                status["containers"] = {"error": "Failed to get container status"}

        return status

    def check_services_status(self) -> dict:
        """Check MCP services status."""
        services_status = {}

        # Read services configuration
        services_file = self.repo_root / "config" / "services.yml"
        if services_file.exists() and HAS_YAML:
            try:
                with open(services_file) as f:
                    services_config = yaml.safe_load(f)

                for service_name, service_config in services_config.get("services", {}).items():
                    service_status = {
                        "configured": True,
                        "enabled": service_config.get("enabled", True),
                        "container_name": service_config.get("container_name", service_name),
                        "port": service_config.get("port"),
                        "health_check": service_config.get("health_check", {}),
                        "status": "unknown",
                    }

                    # Check if container is running
                    if service_status["container_name"] in self.status.get("docker_status", {}).get("containers", {}):
                        container_info = self.status["docker_status"]["containers"][service_status["container_name"]]
                        service_status["status"] = "running" if "Up" in container_info["status"] else "stopped"
                        service_status["container_info"] = container_info
                    else:
                        service_status["status"] = "not_found"

                    services_status[service_name] = service_status

            except Exception as e:
                services_status["error"] = f"Failed to read services config: {e}"
        else:
            services_status["error"] = "Services configuration not found or PyYAML not installed"

        return services_status

    def check_gateway_status(self) -> dict:
        """Check gateway API status."""
        gateway_status = {
            "api_reachable": False,
            "health_check": False,
            "virtual_servers": 0,
            "gateways": 0,
            "response_time": None,
        }

        # Try to reach gateway API
        gateway_urls = ["http://localhost:8080", "http://localhost:3000", "http://localhost:8000"]

        for url in gateway_urls:
            try:
                start_time = time.time()
                if HAS_REQUESTS:
                    response = requests.get(f"{url}/health", timeout=5)
                    response_time = time.time() - start_time

                    if response.status_code == 200:
                        gateway_status["api_reachable"] = True
                        gateway_status["health_check"] = True
                        gateway_status["response_time"] = f"{response_time:.2f}s"
                        gateway_status["url"] = url
                        break
                else:
                    # Fallback to curl
                    result = subprocess.run(
                        ["curl", "-s", "-w", "%{http_code}", f"{url}/health"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0 and "200" in result.stdout:
                        gateway_status["api_reachable"] = True
                        gateway_status["health_check"] = True
                        gateway_status["url"] = url
                        break
            except Exception:  # noqa: S112
                continue

        # Get virtual servers count
        try:
            result = subprocess.run(
                ["make", "list-servers"], cwd=self.repo_root, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Count lines that look like server entries
                server_lines = [
                    line for line in result.stdout.split("\n") if "|" in line and not line.startswith("NAME")
                ]
                gateway_status["virtual_servers"] = len(server_lines)
        except Exception:
            pass

        return gateway_status

    def check_configuration_status(self) -> dict:
        """Check configuration files status."""
        config_status = {}

        # Check .env file
        env_file = self.repo_root / ".env"
        if env_file.exists():
            config_status["env_file"] = "exists"
            with open(env_file) as f:
                env_vars = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value

                # Check critical variables
                critical_vars = ["JWT_SECRET_KEY", "AUTH_ENCRYPTION_SECRET", "PLATFORM_ADMIN_EMAIL"]
                missing_vars = [var for var in critical_vars if var not in env_vars]

                if missing_vars:
                    config_status["env_status"] = f"missing_vars: {', '.join(missing_vars)}"
                else:
                    config_status["env_status"] = "complete"
                    config_status["env_vars_count"] = len(env_vars)
        else:
            config_status["env_file"] = "missing"
            config_status["env_status"] = "not_found"

        # Check services configuration
        services_file = self.repo_root / "config" / "services.yml"
        config_status["services_config"] = "exists" if services_file.exists() else "missing"

        # Check virtual servers configuration
        vservers_file = self.repo_root / "config" / "virtual-servers.txt"
        config_status["virtual_servers_config"] = "exists" if vservers_file.exists() else "missing"

        return config_status

    def check_ide_status(self) -> dict:
        """Check IDE configuration status."""
        ide_status = {}

        try:
            # Use ide-setup.py to get IDE status
            result = subprocess.run(
                ["python3", "scripts/ide-setup.py", "detect"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                detected_ides = result.stdout.strip().replace("Detected IDEs: ", "")
                if detected_ides:
                    ide_status["detected"] = detected_ides.split(", ")
                else:
                    ide_status["detected"] = []

                # Check configuration status for each IDE
                for ide in ["cursor", "windsurf", "vscode", "claude"]:
                    try:
                        status_result = subprocess.run(
                            ["python3", "scripts/ide-setup.py", "setup", ide, "--action", "status"],
                            cwd=self.repo_root,
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        ide_status[ide] = "configured" if status_result.returncode == 0 else "not_configured"
                    except Exception:
                        ide_status[ide] = "unknown"
            else:
                ide_status["error"] = result.stderr.strip()
        except Exception as e:
            ide_status["error"] = str(e)

        return ide_status

    def generate_recommendations(self) -> list[str]:
        """Generate recommendations based on status."""
        recommendations = []

        # Docker recommendations
        docker_status = self.status.get("docker_status", {})
        if docker_status.get("docker") != "running":
            recommendations.append("Start Docker daemon to run MCP Gateway services")

        if docker_status.get("compose") == "not_installed":
            recommendations.append("Install Docker Compose to manage multi-container applications")

        # Configuration recommendations
        config_status = self.status.get("configurations", {})
        if config_status.get("env_file") == "missing":
            recommendations.append("Create .env file with required secrets (run 'make setup')")
        elif config_status.get("env_status") != "complete":
            recommendations.append("Complete .env configuration with missing variables")

        # Gateway recommendations
        gateway_status = self.status.get("gateway_status", {})
        if not gateway_status.get("api_reachable"):
            recommendations.append("Start the gateway stack (run 'make start')")

        # IDE recommendations
        ide_status = self.status.get("ide_status", {})
        detected_ides = ide_status.get("detected", [])
        if detected_ides:
            unconfigured = [ide for ide in detected_ides if ide_status.get(ide) == "not_configured"]
            if unconfigured:
                recommendations.append(
                    f"Configure IDE connections: {', '.join(unconfigured)} (run 'make ide-setup IDE=all')"
                )

        # Service recommendations
        services_status = self.status.get("services", {})
        stopped_services = [
            name
            for name, status in services_status.items()
            if isinstance(status, dict) and status.get("status") == "stopped"
        ]
        if stopped_services:
            recommendations.append(f"Consider starting stopped services: {', '.join(stopped_services)}")

        return recommendations

    def collect_all_status(self):
        """Collect all status information."""
        self.status["docker_status"] = self.check_docker_status()
        self.status["services"] = self.check_services_status()
        self.status["gateway_status"] = self.check_gateway_status()
        self.status["configurations"] = self.check_configuration_status()
        self.status["ide_status"] = self.check_ide_status()
        self.status["recommendations"] = self.generate_recommendations()

        # Determine overall health
        if self.status["gateway_status"].get("api_reachable"):
            self.status["overall_health"] = "healthy"
        elif self.status["docker_status"].get("docker") == "running":
            self.status["overall_health"] = "degraded"
        else:
            self.status["overall_health"] = "unhealthy"

    def print_status(self):
        """Print status information in a readable format."""
        print("=" * 60)
        print("MCP Gateway System Status")
        print("=" * 60)
        print(f"Timestamp: {self.status['timestamp']}")
        print(f"Overall Health: {self.status['overall_health'].upper()}")
        print()

        # Docker Status
        print("🐳 Docker Status:")
        docker = self.status["docker_status"]
        print(f"  Docker: {docker.get('docker', 'unknown')}")
        if docker.get("docker_version"):
            print(f"  Version: {docker['docker_version']}")
        print(f"  Docker Compose: {docker.get('compose', 'unknown')}")

        if docker.get("containers"):
            print(f"  Containers: {len(docker['containers'])} running")
            if self.detailed:
                for name, info in docker["containers"].items():
                    status_icon = "✅" if "Up" in info["status"] else "❌"
                    print(f"    {status_icon} {name}: {info['status']}")
        print()

        # Gateway Status
        print("🌐 Gateway Status:")
        gateway = self.status["gateway_status"]
        api_icon = "✅" if gateway.get("api_reachable") else "❌"
        print(f"  {api_icon} API Reachable: {gateway.get('api_reachable', 'unknown')}")
        if gateway.get("response_time"):
            print(f"  Response Time: {gateway['response_time']}")
        print(f"  Virtual Servers: {gateway.get('virtual_servers', 0)}")
        print()

        # Services Status
        print("🔧 Services Status:")
        services = self.status["services"]
        if "error" in services:
            print(f"  ❌ Error: {services['error']}")
        else:
            for name, status in services.items():
                if isinstance(status, dict):
                    status_icon = "✅" if status.get("status") == "running" else "❌"
                    enabled_icon = "🟢" if status.get("enabled") else "🔴"
                    print(f"  {status_icon} {enabled_icon} {name}: {status.get('status', 'unknown')}")
                    if self.detailed and status.get("port"):
                        print(f"      Port: {status['port']}")
        print()

        # Configuration Status
        print("⚙️ Configuration Status:")
        config = self.status["configurations"]
        config_icon = "✅" if config.get("env_status") == "complete" else "❌"
        print(f"  {config_icon} .env File: {config.get('env_status', 'unknown')}")
        print(f"  Services Config: {config.get('services_config', 'unknown')}")
        print(f"  Virtual Servers Config: {config.get('virtual_servers_config', 'unknown')}")
        print()

        # IDE Status
        print("💻 IDE Status:")
        ide = self.status["ide_status"]
        if "error" in ide:
            print(f"  ❌ Error: {ide['error']}")
        else:
            detected = ide.get("detected", [])
            if detected:
                print(f"  Detected IDEs: {', '.join(detected)}")
                for ide_name in detected:
                    status_icon = "✅" if ide.get(ide_name) == "configured" else "❌"
                    print(f"    {status_icon} {ide_name}: {ide.get(ide_name, 'unknown')}")
            else:
                print("  No IDEs detected")
        print()

        # Recommendations
        if self.status["recommendations"]:
            print("💡 Recommendations:")
            for i, rec in enumerate(self.status["recommendations"], 1):
                print(f"  {i}. {rec}")
            print()

        # Quick Actions
        print("🚀 Quick Actions:")
        print("  make start              # Start the gateway stack")
        print("  make register           # Register gateways and servers")
        print("  make jwt               # Generate JWT token")
        print("  make ide-setup IDE=all  # Configure all IDEs")
        print("  make setup              # Run interactive setup wizard")
        print("  make help               # Show all available commands")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Show MCP Gateway system status")
    parser.add_argument("--detailed", action="store_true", help="Show detailed status information")
    parser.add_argument("--json", action="store_true", help="Output status as JSON")
    args = parser.parse_args()

    status_checker = SystemStatus(detailed=args.detailed)
    status_checker.collect_all_status()

    if args.json:
        print(json.dumps(status_checker.status, indent=2))
    else:
        status_checker.print_status()


if __name__ == "__main__":
    main()
