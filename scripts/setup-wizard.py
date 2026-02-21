#!/usr/bin/env python3
"""
Interactive Setup Wizard for MCP Gateway

Phase 3: Command Simplification
Consolidates setup, setup-dev, ide-setup, and configuration management
into a unified interactive experience.

Features:
- Step-by-step configuration wizard
- Environment detection and validation
- IDE setup and management
- Authentication configuration
- Service registration
- Configuration validation
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import re


@dataclass
class SetupConfig:
    """Configuration collected during setup."""
    # Environment settings
    gateway_url: str = "http://localhost:4444"
    server_port: int = 4444
    environment: str = "development"

    # Authentication
    jwt_secret: Optional[str] = None
    auth_secret: Optional[str] = None
    auto_generate_secrets: bool = True

    # IDE configuration
    configure_ides: bool = True
    selected_ides: List[str] = None
    ide_configs: Dict[str, Any] = None

    # Services
    start_services: bool = True
    register_servers: bool = True
    wait_for_ready: bool = True

    # Development
    setup_dev_environment: bool = True
    install_dependencies: bool = True
    configure_git_hooks: bool = True

    # Validation
    run_validation: bool = True
    test_connection: bool = True


class SetupWizard:
    """Interactive setup wizard for MCP Gateway."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.scripts_dir = self.repo_root / "scripts"
        self.data_dir = self.repo_root / "data"
        self.config_dir = self.repo_root / "config"
        self.env_file = self.repo_root / ".env"

        self.config = SetupConfig()
        self.steps = [
            ("Welcome", self._welcome_step),
            ("Environment", self._environment_step),
            ("Authentication", self._auth_step),
            ("IDE Setup", self._ide_step),
            ("Services", self._services_step),
            ("Development", self._development_step),
            ("Validation", self._validation_step),
            ("Complete", self._complete_step),
        ]

    def _print_header(self, title: str):
        """Print step header."""
        width = 60
        border = "=" * width
        print(f"\n{border}")
        print(f"{title:^{width}}")
        print(f"{border}")

    def _print_section(self, title: str):
        """Print section header."""
        print(f"\n🔧 {title}")
        print("-" * len(title))

    def _get_input(self, prompt: str, default: str = "", validator=None) -> str:
        """Get user input with validation."""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "

        while True:
            try:
                user_input = input(prompt).strip()
                if not user_input and default:
                    user_input = default

                if validator and user_input:
                    if validator(user_input):
                        return user_input
                    else:
                        print(f"❌ Invalid input. Please try again.")
                else:
                    return user_input
            except KeyboardInterrupt:
                print("\n\n❌ Setup cancelled.")
                sys.exit(1)

    def _get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input."""
        default_str = "Y/n" if default else "y/N"
        while True:
            response = self._get_input(f"{prompt} ({default_str})", "").lower()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'.")

    def _get_choice(self, prompt: str, choices: List[str], default: str = "") -> str:
        """Get choice from list."""
        print(f"\nAvailable options:")
        for i, choice in enumerate(choices, 1):
            marker = "→" if choice == default else " "
            print(f"  {marker} {i}. {choice}")

        while True:
            try:
                response = self._get_input(f"{prompt}", default).strip()
                if not response and default:
                    return default

                # Try by number
                try:
                    idx = int(response) - 1
                    if 0 <= idx < len(choices):
                        return choices[idx]
                except ValueError:
                    pass

                # Try by name
                if response in choices:
                    return response

                print(f"❌ Invalid choice. Please enter a number or name.")
            except KeyboardInterrupt:
                print("\n\n❌ Setup cancelled.")
                sys.exit(1)

    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None

    def _validate_port(self, port: str) -> bool:
        """Validate port number."""
        try:
            p = int(port)
            return 1 <= p <= 65535
        except ValueError:
            return False

    def _detect_ides(self) -> List[str]:
        """Detect installed IDEs."""
        detected = []
        home = Path.home()

        # Check for Cursor
        if (home / ".cursor" / "settings.json").exists():
            detected.append("cursor")

        # Check for VSCode
        if (home / ".vscode" / "settings.json").exists():
            detected.append("vscode")

        # Check for Windsurf
        if (home / ".windsurf" / "settings.json").exists():
            detected.append("windsurf")

        # Check for Claude Desktop
        if (home / ".config" / "claude" / "claude_desktop_config.json").exists():
            detected.append("claude")

        return detected

    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """Run command and return success, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def _generate_secrets(self) -> Tuple[str, str]:
        """Generate JWT and auth secrets."""
        import secrets

        jwt_secret = secrets.token_urlsafe(32)
        auth_secret = secrets.token_urlsafe(32)

        return jwt_secret, auth_secret

    def _update_env_file(self):
        """Update .env file with configuration."""
        env_vars = {}

        # Load existing .env
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key] = value

        # Update with new configuration
        env_vars['GATEWAY_URL'] = self.config.gateway_url
        env_vars['SERVER_PORT'] = str(self.config.server_port)
        env_vars['ENVIRONMENT'] = self.config.environment

        if self.config.jwt_secret:
            env_vars['JWT_SECRET_KEY'] = self.config.jwt_secret
        if self.config.auth_secret:
            env_vars['AUTH_ENCRYPTION_SECRET'] = self.config.auth_secret

        # Write .env file
        with open(self.env_file, 'w') as f:
            f.write("# MCP Gateway Configuration\n")
            f.write(f"# Generated by setup wizard at {datetime.now().isoformat()}\n\n")

            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        print(f"✅ Configuration saved to {self.env_file}")

    def _welcome_step(self) -> bool:
        """Welcome step."""
        self._print_header("Welcome to MCP Gateway Setup")

        print("""
🚀 MCP Gateway Setup Wizard

This wizard will help you configure your MCP Gateway environment with:
• Environment configuration
• Authentication setup
• IDE integration
• Service management
• Development environment
• Validation and testing

Let's get started!
        """)

        return self._get_yes_no("Continue with setup?", True)

    def _environment_step(self) -> bool:
        """Environment configuration step."""
        self._print_section("Environment Configuration")

        print("Configure your MCP Gateway environment settings.\n")

        # Gateway URL
        self.config.gateway_url = self._get_input(
            "Gateway URL",
            self.config.gateway_url,
            self._validate_url
        )

        # Server port
        default_port = str(self.config.server_port)
        port = self._get_input(
            "Server port",
            default_port,
            self._validate_port
        )
        self.config.server_port = int(port)

        # Environment
        environments = ["development", "staging", "production"]
        self.config.environment = self._get_choice(
            "Environment type",
            environments,
            self.config.environment
        )

        print(f"\n✅ Environment configured:")
        print(f"   URL: {self.config.gateway_url}")
        print(f"   Port: {self.config.server_port}")
        print(f"   Environment: {self.config.environment}")

        return True

    def _auth_step(self) -> bool:
        """Authentication configuration step."""
        self._print_section("Authentication Configuration")

        print("Configure authentication for secure API access.\n")

        # Check if secrets already exist
        existing_secrets = False
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                content = f.read()
                if 'JWT_SECRET_KEY=' in content and 'AUTH_ENCRYPTION_SECRET=' in content:
                    existing_secrets = True

        if existing_secrets:
            print("🔑 Existing secrets found in .env file")
            if not self._get_yes_no("Generate new secrets?", False):
                # Load existing secrets
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if line.startswith('JWT_SECRET_KEY='):
                            self.config.jwt_secret = line.split('=', 1)[1].strip()
                        elif line.startswith('AUTH_ENCRYPTION_SECRET='):
                            self.config.auth_secret = line.split('=', 1)[1].strip()
                return True

        # Generate new secrets
        self.config.auto_generate_secrets = self._get_yes_no(
            "Auto-generate secure secrets?",
            True
        )

        if self.config.auto_generate_secrets:
            self.config.jwt_secret, self.config.auth_secret = self._generate_secrets()
            print("✅ Secure secrets generated")
        else:
            self.config.jwt_secret = self._get_input("JWT Secret Key")
            self.config.auth_secret = self._get_input("Auth Encryption Secret")

        return True

    def _ide_step(self) -> bool:
        """IDE configuration step."""
        self._print_section("IDE Configuration")

        print("Configure IDE integration for seamless MCP access.\n")

        # Detect installed IDEs
        detected = self._detect_ides()
        available_ides = ["cursor", "vscode", "windsurf", "claude"]

        print(f"Detected IDEs: {', '.join(detected) if detected else 'None'}")

        self.config.configure_ides = self._get_yes_no(
            "Configure IDE integration?",
            True
        )

        if not self.config.configure_ides:
            return True

        # Select IDEs
        if detected:
            print("\nDetected IDEs will be configured by default.")
            self.config.selected_ides = detected.copy()

            # Ask about additional IDEs
            additional = [ide for ide in available_ides if ide not in detected]
            if additional and self._get_yes_no("Configure additional IDEs?", False):
                for ide in additional:
                    if self._get_yes_no(f"Configure {ide.title()}?", False):
                        self.config.selected_ides.append(ide)
        else:
            # No IDEs detected, let user choose
            self.config.selected_ides = []
            for ide in available_ides:
                if self._get_yes_no(f"Configure {ide.title()}?", False):
                    self.config.selected_ides.append(ide)

        if not self.config.selected_ides:
            print("⚠️  No IDEs selected for configuration.")

        return True

    def _services_step(self) -> bool:
        """Services configuration step."""
        self._print_section("Services Configuration")

        print("Configure MCP Gateway services.\n")

        self.config.start_services = self._get_yes_no(
            "Start MCP Gateway services?",
            True
        )

        if self.config.start_services:
            self.config.register_servers = self._get_yes_no(
                "Register virtual servers?",
                True
            )

            if self.config.register_servers:
                self.config.wait_for_ready = self._get_yes_no(
                    "Wait for services to be ready?",
                    True
                )

        return True

    def _development_step(self) -> bool:
        """Development environment step."""
        self._print_section("Development Environment")

        print("Configure development environment and tools.\n")

        self.config.setup_dev_environment = self._get_yes_no(
            "Setup development environment?",
            True
        )

        if self.config.setup_dev_environment:
            self.config.install_dependencies = self._get_yes_no(
                "Install/update dependencies?",
                True
            )

            self.config.configure_git_hooks = self._get_yes_no(
                "Configure Git hooks?",
                True
            )

        return True

    def _validation_step(self) -> bool:
        """Validation step."""
        self._print_section("Validation and Testing")

        print("Validate configuration and test connections.\n")

        self.config.run_validation = self._get_yes_no(
            "Run configuration validation?",
            True
        )

        if self.config.run_validation:
            self.config.test_connection = self._get_yes_no(
                "Test gateway connection?",
                True
            )

        return True

    def _complete_step(self) -> bool:
        """Completion step."""
        self._print_header("Setup Complete!")

        print("""
🎉 MCP Gateway setup is complete!

Configuration Summary:
""")

        summary_items = [
            f"Environment: {self.config.environment}",
            f"Gateway URL: {self.config.gateway_url}",
            f"Server Port: {self.config.server_port}",
            f"Authentication: {'✅ Configured' if self.config.jwt_secret else '❌ Not configured'}",
            f"IDEs: {', '.join(self.config.selected_ides) if self.config.selected_ides else 'None'}",
            f"Services: {'✅ Will start' if self.config.start_services else '❌ Manual start'}",
            f"Development: {'✅ Configured' if self.config.setup_dev_environment else '❌ Not configured'}",
        ]

        for item in summary_items:
            print(f"  • {item}")

        print(f"\nConfiguration saved to: {self.env_file}")

        # Next steps
        print(f"""
📋 Next Steps:
1. Review configuration in .env file
2. Start services: make start
3. Register servers: make register
4. Test with: make status

📚 Documentation:
• README.md for usage instructions
• docs/ for detailed guides
• make help for available commands

🐛 Issues?
• Check logs: make logs
• Reset database: make reset-db
• Get help: make help
        """)

        return True

    def _execute_setup(self):
        """Execute the actual setup based on configuration."""
        print("\n🔧 Applying configuration...")

        # Update .env file
        self._update_env_file()

        # IDE configuration
        if self.config.configure_ides and self.config.selected_ides:
            print("\n🔧 Configuring IDEs...")
            for ide in self.config.selected_ides:
                success, stdout, stderr = self._run_command([
                    sys.executable,
                    str(self.scripts_dir / "ide-setup.py"),
                    "--ide", ide
                ])
                if success:
                    print(f"✅ {ide.title()} configured")
                else:
                    print(f"❌ {ide.title()} configuration failed: {stderr}")

        # Start services
        if self.config.start_services:
            print("\n🚀 Starting MCP Gateway services...")
            success, stdout, stderr = self._run_command(["./start.sh"])
            if success:
                print("✅ Services started")
            else:
                print(f"❌ Failed to start services: {stderr}")

        # Register servers
        if self.config.register_servers:
            print("\n📝 Registering virtual servers...")
            cmd = [str(self.scripts_dir / "gateway" / "register.sh")]
            if self.config.wait_for_ready:
                cmd.append("--wait")

            success, stdout, stderr = self._run_command(cmd)
            if success:
                print("✅ Servers registered")
            else:
                print(f"❌ Failed to register servers: {stderr}")

        # Development environment
        if self.config.setup_dev_environment:
            print("\n💻 Setting up development environment...")

            if self.config.install_dependencies:
                print("Installing dependencies...")
                success, stdout, stderr = self._run_command(["npm", "install"])
                if success:
                    print("✅ Dependencies installed")
                else:
                    print(f"❌ Failed to install dependencies: {stderr}")

            if self.config.configure_git_hooks:
                print("Configuring Git hooks...")
                success, stdout, stderr = self._run_command(["make", "pre-commit-install"])
                if success:
                    print("✅ Git hooks configured")
                else:
                    print(f"❌ Failed to configure Git hooks: {stderr}")

        # Validation
        if self.config.run_validation:
            print("\n✅ Running validation...")
            success, stdout, stderr = self._run_command(["make", "validate-config"])
            if success:
                print("✅ Configuration validated")
            else:
                print(f"❌ Validation failed: {stderr}")

        # Test connection
        if self.config.test_connection:
            print("\n🔗 Testing connection...")
            success, stdout, stderr = self._run_command(["make", "status"])
            if success:
                print("✅ Connection test passed")
            else:
                print(f"❌ Connection test failed: {stderr}")

    def run(self):
        """Run the interactive setup wizard."""
        try:
            for step_name, step_func in self.steps:
                if not step_func():
                    print(f"\n❌ Setup cancelled at {step_name} step.")
                    return False

            # Execute setup
            self._execute_setup()

            print(f"\n🎉 Setup completed successfully!")
            return True

        except KeyboardInterrupt:
            print(f"\n\n❌ Setup cancelled by user.")
            return False
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive MCP Gateway Setup Wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run interactive setup
  %(prog)s --quick            # Quick setup with defaults
  %(prog)s --reconfigure      # Reconfigure existing setup
        """
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick setup with default values"
    )

    parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="Reconfigure existing setup"
    )

    args = parser.parse_args()

    wizard = SetupWizard()

    if args.quick:
        print("🚀 Quick setup mode - using default configuration...")
        # Apply defaults and run setup
        wizard.config.auto_generate_secrets = True
        wizard.config.jwt_secret, wizard.config.auth_secret = wizard._generate_secrets()
        wizard._execute_setup()
    elif args.reconfigure:
        print("🔧 Reconfigure mode - updating existing setup...")
        wizard.run()
    else:
        wizard.run()


if __name__ == "__main__":
    main()
