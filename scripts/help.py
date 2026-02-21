#!/usr/bin/env python3
"""
Enhanced Help System for MCP Gateway

Phase 3: Command Simplification
Provides contextual help with examples and interactive command discovery.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class HelpSystem:
    """Enhanced help system for MCP Gateway."""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.makefile = self.repo_root / "Makefile"
        self.commands = {}
        self.topics = {}
        self.examples = {}
        self.load_makefile_commands()
    
    def load_makefile_commands(self):
        """Load commands from Makefile."""
        if not self.makefile.exists():
            return
        
        with open(self.makefile, 'r') as f:
            content = f.read()
        
        # Parse Makefile targets
        lines = content.split('\n')
        current_target = None
        current_description = ""
        
        for line in lines:
            line = line.rstrip()
            
            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue
            
            # Check for target definition
            if ':' in line and not line.startswith('\t'):
                parts = line.split(':', 1)
                target = parts[0].strip()
                
                # Skip special targets
                if target.startswith('.') or target == 'DEFAULT_GOAL':
                    continue
                
                # Save previous target
                if current_target:
                    self.commands[current_target] = current_description.strip()
                
                current_target = target
                current_description = parts[1].strip() if len(parts) > 1 else ""
            
            # Check for description in same line
            elif current_target and '##' in line:
                current_description = line.split('##', 1)[1].strip()
        
        # Save last target
        if current_target:
            self.commands[current_target] = current_description.strip()
    
    def show_help(self, topic: Optional[str] = None, examples: bool = False):
        """Show help information."""
        if examples:
            self.show_examples()
        elif topic:
            self.show_topic_help(topic)
        else:
            self.show_main_help()
    
    def show_main_help(self):
        """Show main help overview."""
        print("=" * 60)
        print("MCP Gateway - Enhanced Help System")
        print("=" * 60)
        print()
        print("MCP Gateway is a self-hosted aggregation gateway that consolidates")
        print("multiple Model Context Protocol (MCP) servers into a single connection.")
        print()
        print("🚀 Quick Start:")
        print("  make setup              # Interactive configuration wizard")
        print("  make start              # Start the gateway stack")
        print("  make register           # Register gateways and servers")
        print("  make jwt               # Generate JWT token")
        print("  make ide-setup IDE=all  # Configure IDE connections")
        print("  make status            # Check system status")
        print()
        print("📋 Available Help Topics:")
        print("  setup           - Initial setup and configuration")
        print("  ide             - IDE configuration and management")
        print("  services        - Service management and monitoring")
        print("  gateway         - Gateway operations and API")
        print("  docker          - Docker and container management")
        print("  development     - Development tools and workflows")
        print("  troubleshooting  - Common issues and solutions")
        print("  examples        - Practical command examples")
        print()
        print("🔧 Command Categories:")
        self.show_command_categories()
        print()
        print("💡 Getting Help:")
        print("  make help               # Show this help")
        print("  make help TOPIC        # Get help on specific topic")
        print("  make help-examples      # Show practical examples")
        print("  make status            # Check system status for recommendations")
        print()
        print("📚 Documentation:")
        print("  PROJECT_CONTEXT.md    # Complete project documentation")
        print("  README.md              # Setup and usage guide")
        print("  CHANGELOG.md           # Version history and changes")
        print("  docs/                  # Comprehensive documentation")
        print()
    
    def show_command_categories(self):
        """Show commands organized by category."""
        categories = {
            "🚀 Getting Started": ["setup", "start", "register", "jwt", "ide-setup"],
            "🔧 System Management": ["stop", "reset-db", "cleanup-duplicates", "status"],
            "🌐 Gateway Operations": ["list-prompts", "list-servers", "register-enhanced"],
            "💻 IDE Configuration": ["config-backup", "config-restore", "config-install", "config-list"],
            "🧪 Development": ["lint", "format", "test", "deps-check", "deps-update"],
            "🔒 Quality & Security": ["shellcheck", "pre-commit-install", "pre-commit-run"],
            "📖 Help & Documentation": ["help", "help-topics", "help-examples"]
        }
        
        for category, commands in categories.items():
            print(f"  {category}:")
            for cmd in commands:
                if cmd in self.commands:
                    description = self.commands[cmd]
                    print(f"    make {cmd:<20} # {description}")
                else:
                    print(f"    make {cmd:<20} # Command not found")
            print()
    
    def show_topic_help(self, topic: str):
        """Show detailed help for a specific topic."""
        topic = topic.lower()
        
        if topic == "setup":
            self.show_setup_help()
        elif topic == "ide":
            self.show_ide_help()
        elif topic == "services":
            self.show_services_help()
        elif topic == "gateway":
            self.show_gateway_help()
        elif topic == "docker":
            self.show_docker_help()
        elif topic == "development":
            self.show_development_help()
        elif topic == "troubleshooting":
            self.show_troubleshooting_help()
        elif topic == "examples":
            self.show_examples()
        else:
            print(f"Topic '{topic}' not found. Available topics:")
            print("  setup, ide, services, gateway, docker, development, troubleshooting, examples")
            print()
            print("Use 'make help-topics' to see all available topics.")
    
    def show_setup_help(self):
        """Show setup help."""
        print("=" * 60)
        print("Setup and Configuration")
        print("=" * 60)
        print()
        print("🚀 Initial Setup:")
        print("  make setup              # Interactive configuration wizard")
        print("    - Checks prerequisites (Docker, Node.js, Python)")
        print("    - Sets up security secrets")
        print("    - Configures IDE connections")
        print("    - Sets up development environment")
        print()
        print("🔑 Security Setup:")
        print("  make generate-secrets   # Generate JWT and encryption secrets")
        print("  make setup-dev          # Set up development environment")
        print()
        print("⚙️ Configuration Files:")
        print("  .env                    # Environment variables and secrets")
        print("  config/services.yml     # Service definitions")
        print("  config/virtual-servers.txt  # Virtual server configurations")
        print()
        print("📋 Setup Checklist:")
        print("  ✅ Docker and Docker Compose installed")
        print("  ✅ Python 3.9+ and Node.js installed")
        print("  ✅ .env file configured with secrets")
        print("  ✅ Services configured in config/services.yml")
        print("  ✅ IDE connections configured (optional)")
        print()
    
    def show_ide_help(self):
        """Show IDE configuration help."""
        print("=" * 60)
        print("IDE Configuration and Management")
        print("=" * 60)
        print()
        print("💻 Supported IDEs:")
        print("  - Cursor (AI-powered code editor)")
        print("  - VSCode (Visual Studio Code)")
        print("  - Windsurf (AI code editor)")
        print("  - Claude Desktop (Anthropic's Claude)")
        print()
        print("🔧 IDE Setup Commands:")
        print("  make ide-setup IDE=<ide> [ACTION=<action>]")
        print("    IDE: cursor, windsurf, vscode, claude, all")
        print("    ACTION: install (default), backup, restore, status")
        print()
        print("📋 Examples:")
        print("  make ide-setup IDE=cursor                    # Install Cursor")
        print("  make ide-setup IDE=all                       # Install all IDEs")
        print("  make ide-setup IDE=vscode ACTION=backup      # Backup VS Code")
        print("  make ide-setup IDE=windsurf ACTION=status     # Check Windsurf")
        print()
        print("🔄 IDE Management:")
        print("  make config-backup       # Backup all IDE configurations")
        print("  make config-restore IDE=<ide>  # Restore specific IDE")
        print("  make config-list          # List available backups")
        print("  make config-cleanup      # Clean up old backups")
        print()
        print("📁 IDE Configuration Locations:")
        print("  Cursor: ~/.cursor/mcp.json")
        print("  VSCode: ~/.vscode/settings.json")
        print("  Windsurf: ~/.windsurf/mcp.json")
        print("  Claude: ~/.config/claude/claude_desktop_config.json")
        print()
    
    def show_services_help(self):
        """Show services management help."""
        print("=" * 60)
        print("Service Management and Monitoring")
        print("=" * 60)
        print()
        print("🔧 Service Commands:")
        print("  make start              # Start all services")
        print("  make stop               # Stop all services")
        print("  make gateway-only       # Start only gateway service")
        print("  make status            # Check service status")
        print()
        print("📊 Service Information:")
        print("  make list-servers       # List virtual servers")
        print("  make list-prompts       # List available prompts")
        print("  make register-enhanced  # Register with enhanced features")
        print()
        print("🧹 Service Maintenance:")
        print("  make cleanup-duplicates # Remove duplicate servers")
        print("  make reset-db           # Reset database (WARNING)")
        print()
        print("⚙️ Service Configuration:")
        print("  config/services.yml     # Service definitions and settings")
        print("  config/scaling-policies.yml  # Auto-scaling policies")
        print("  config/sleep_settings.yml      # Sleep/wake settings")
        print()
    
    def show_gateway_help(self):
        """Show gateway operations help."""
        print("=" * 60)
        print("Gateway Operations and API")
        print("=" * 60)
        print()
        print("🌐 Gateway Commands:")
        print("  make register           # Register gateways and servers")
        print("  make register-wait      # Register with wait for readiness")
        print("  make jwt               # Generate JWT token for API access")
        print()
        print("🔐 Authentication:")
        print("  JWT tokens are required for API access")
        print("  Default expiry: 7 days")
        print("  Set PLATFORM_ADMIN_EMAIL in .env")
        print()
        print("📊 Gateway API:")
        print("  Health check: GET /health")
        print("  Virtual servers: GET /servers")
        print("  Prompts: GET /prompts")
        print("  Tool router: POST /route")
        print()
        print("🔑 Required Environment Variables:")
        print("  JWT_SECRET_KEY         # JWT signing secret (32+ chars)")
        print("  AUTH_ENCRYPTION_SECRET # Encryption secret (32+ chars)")
        print("  PLATFORM_ADMIN_EMAIL   # Admin email for JWT")
        print()
    
    def show_docker_help(self):
        """Show Docker help."""
        print("=" * 60)
        print("Docker and Container Management")
        print("=" * 60)
        print()
        print("🐳 Docker Commands:")
        print("  make start              # Start with Docker Compose")
        print("  make stop               # Stop all containers")
        print("  make gateway-only       # Start only gateway")
        print("  make status            # Check container status")
        print()
        print("📋 Docker Files:")
        print("  docker-compose.yml     # Main service definitions")
        print("  Dockerfile.*            # Service container definitions")
        print("  .dockerignore           # Docker ignore patterns")
        print()
        print("🔧 Docker Operations:")
        print("  docker ps               # List running containers")
        print("  docker logs <service>   # View service logs")
        print("  docker exec -it <service> bash  # Access container shell")
        print("  docker-compose logs    # View all logs")
        print("  docker-compose down    # Stop and remove containers")
        print()
        print("⚡ Performance:")
        print("  Services auto-sleep when idle")
        print("  Sub-200ms wake times for sleeping services")
        print("  Resource limits configured for all services")
        print()
    
    def show_development_help(self):
        """Show development help."""
        print("=" * 60)
        print("Development Tools and Workflows")
        print("=" * 60)
        print()
        print("🧪 Code Quality:")
        print("  make lint               # Run all linters")
        print("  make lint-python        # Lint Python code")
        print("  make lint-typescript    # Lint TypeScript code")
        print("  make shellcheck         # Lint shell scripts")
        print()
        print("📝 Code Formatting:")
        print("  make format             # Format all code")
        print("  make format-python      # Format Python code")
        print("  make format-typescript  # Format TypeScript code")
        print()
        print("🧪 Testing:")
        print("  make test               # Run Python tests")
        print("  make test-coverage     # Run tests with coverage")
        print()
        print("📦 Dependencies:")
        print("  make deps-check         # Check for updates")
        print("  make deps-update        # Update dependencies")
        print()
        print("🔒 Pre-commit Hooks:")
        print("  make pre-commit-install # Install hooks")
        print("  make pre-commit-run     # Run hooks on all files")
        print("  make pre-commit-update  # Update hook versions")
        print()
        print("📊 Coverage Requirements:")
        print("  Minimum 80% test coverage")
        print("  Coverage reports in HTML and XML")
        print("  Automatic coverage upload to Codecov")
        print()
    
    def show_troubleshooting_help(self):
        """Show troubleshooting help."""
        print("=" * 60)
        print("Troubleshooting Common Issues")
        print("=" * 60)
        print()
        print("🚫 Gateway Not Starting:")
        print("  1. Check Docker: docker --version")
        print("  2. Check ports: lsof -i :8080")
        print("  3. Check logs: docker-compose logs")
        print("  4. Reset: make reset-db && make start")
        print()
        print("🔑 JWT Token Issues:")
        print("  1. Check .env file exists")
        print("  2. Verify JWT_SECRET_KEY (32+ chars)")
        print("  3. Check PLATFORM_ADMIN_EMAIL")
        print("  4. Regenerate: make jwt")
        print()
        print("💻 IDE Connection Issues:")
        print("  1. Check IDE detection: python3 scripts/ide-setup.py detect")
        print("  2. Verify config: make ide-setup IDE=<ide> ACTION=status")
        print("  3. Check wrapper script: ls scripts/cursor-mcp-wrapper.sh")
        print("  4. Test connection: curl -H 'Authorization: Bearer <JWT>' localhost:8080")
        print()
        print("🐳 Container Issues:")
        print("  1. Check disk space: df -h")
        print("  2. Check memory: docker stats")
        print("  3. Restart service: docker-compose restart <service>")
        print("  4. Rebuild: docker-compose up --build")
        print()
        print("📋 Performance Issues:")
        print("  1. Check resource usage: make status --detailed")
        print("  2. Monitor with: docker stats")
        print("  3. Check service logs for errors")
        print("  4. Verify service health: curl localhost:8080/health")
        print()
    
    def show_examples(self):
        """Show practical command examples."""
        print("=" * 60)
        print("Practical Command Examples")
        print("=" * 60)
        print()
        print("🚀 First Time Setup:")
        print("  make setup")
        print("  make start")
        print("  make register")
        print("  make jwt")
        print("  make ide-setup IDE=all")
        print()
        print("🔄 Daily Development:")
        print("  make start")
        print("  make status")
        print("  make lint && make test")
        print("  make format")
        print()
        print("💻 IDE Configuration:")
        print("  # Configure new IDE")
        print("  make ide-setup IDE=cursor")
        print("  # Backup before changes")
        print("  make config-backup")
        print("  # Restore if needed")
        print("  make config-restore IDE=cursor")
        print()
        print("🔧 Service Management:")
        print("  # Check all services")
        print("  make status --detailed")
        print("  # Restart specific service")
        print("  docker-compose restart gateway")
        print("  # View logs")
        print("  docker-compose logs gateway")
        print()
        print("🧪 Quality Assurance:")
        print("  # Full check before commit")
        print("  make lint && make test && make test-coverage")
        print("  # Format code")
        print("  make format")
        print("  # Run pre-commit hooks")
        print("  make pre-commit-run")
        print()
        print("📊 Monitoring:")
        print("  # Quick status check")
        print("  make status")
        print("  # Detailed system info")
        print("  make status --detailed")
        print("  # JSON output for scripts")
        print("  python3 scripts/status.py --json")
        print()
        print("🔐 API Testing:")
        print("  # Generate JWT")
        print("  TOKEN=$(make jwt | tail -1)")
        print("  # Test API")
        print("  curl -H \"Authorization: Bearer $TOKEN\" localhost:8080/health")
        print("  # List servers")
        print("  curl -H \"Authorization: Bearer $TOKEN\" localhost:8080/servers")
        print()
        print("🛠️ Advanced Operations:")
        print("  # Clean reset")
        print("  make clean && make start && make register")
        print("  # Update dependencies")
        print("  make deps-update")
        print("  # Full test suite")
        print("  make test-coverage")
        print("  # Security scan")
        print("  make shellcheck")
        print()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enhanced help system for MCP Gateway")
    parser.add_argument("topic", nargs="?", help="Help topic to display")
    parser.add_argument("--examples", action="store_true", help="Show practical examples")
    args = parser.parse_args()
    
    help_system = HelpSystem()
    help_system.show_help(args.topic, args.examples)

if __name__ == "__main__":
    main()
