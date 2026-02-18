#!/usr/bin/env python3
"""
Enhanced Command System for MCP Gateway

Phase 3: Command Simplification
Provides unified command interface with options and subcommands.

Consolidated Commands:
- setup: Interactive wizard (replaces setup, setup-dev, ide-setup)
- auth: Authentication management (replaces jwt, auth, auth-check, auth-refresh)
- start: Start services (replaces start, gateway-only, with --options)
- stop: Stop services
- register: Register servers (replaces register, register-wait, with --wait)
- status: System status (replaces status, status-detailed, status-json)
- list: List resources (replaces list-servers, list-prompts)
- clean: Clean up (replaces clean, reset-db, cleanup-duplicates)
- lint: Run linters (replaces lint, lint-python, lint-typescript, shellcheck)
- format: Format code (replaces format, format-python, format-typescript)
- test: Run tests (replaces test, test-coverage)
- config: Configuration management (replaces config-* commands)
- help: Enhanced help system (replaces help, help-topics, help-examples)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    output: str
    error: str
    duration: float = 0.0


class CommandManager:
    """Unified command management for MCP Gateway."""
    
    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.makefile = self.repo_root / "Makefile"
        
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> CommandResult:
        """Run command and return result."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            duration = time.time() - start_time
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                duration=duration
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CommandResult(
                success=False,
                output="",
                error="Command timed out",
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                duration=duration
            )
            
    def _run_make(self, target: str, args: List[str] = None) -> CommandResult:
        """Run make target with optional arguments."""
        cmd = ["make", target]
        if args:
            cmd.extend(args)
        return self._run_command(cmd)
        
    def setup(self, args: argparse.Namespace) -> CommandResult:
        """Setup command - interactive configuration wizard."""
        cmd = [sys.executable, str(self.repo_root / "scripts" / "setup-wizard.py")]
        
        if args.quick:
            cmd.append("--quick")
        elif args.reconfigure:
            cmd.append("--reconfigure")
            
        return self._run_command(cmd)
        
    def auth(self, args: argparse.Namespace) -> CommandResult:
        """Authentication management command."""
        if args.generate:
            return self._run_make("generate-secrets")
        elif args.check:
            return self._run_make("auth-check")
        elif args.refresh:
            return self._run_make("auth-refresh")
        else:
            # Default: generate JWT token
            return self._run_make("jwt")
            
    def start(self, args: argparse.Namespace) -> CommandResult:
        """Start services command."""
        make_args = []
        
        if args.gateway_only:
            make_args.append("gateway-only")
            
        return self._run_make("start", make_args)
        
    def stop(self, args: argparse.Namespace) -> CommandResult:
        """Stop services command."""
        return self._run_make("stop")
        
    def register(self, args: argparse.Namespace) -> CommandResult:
        """Register servers command."""
        make_args = []
        
        if args.wait:
            make_args.append("register-wait")
        else:
            make_args.append("register")
            
        return self._run_make("register", make_args)
        
    def status(self, args: argparse.Namespace) -> CommandResult:
        """System status command."""
        if args.detailed:
            return self._run_make("status-detailed")
        elif args.json:
            return self._run_make("status-json")
        else:
            return self._run_make("status")
            
    def list(self, args: argparse.Namespace) -> CommandResult:
        """List resources command."""
        if args.servers:
            return self._run_make("list-servers")
        elif args.prompts:
            return self._run_make("list-prompts")
        else:
            # Default: list both
            servers_result = self._run_make("list-servers")
            prompts_result = self._run_make("list-prompts")
            
            combined_output = "=== Virtual Servers ===\n"
            combined_output += servers_result.output
            combined_output += "\n=== Available Prompts ===\n"
            combined_output += prompts_result.output
            
            return CommandResult(
                success=servers_result.success and prompts_result.success,
                output=combined_output,
                error=servers_result.error or prompts_result.error
            )
            
    def clean(self, args: argparse.Namespace) -> CommandResult:
        """Clean up command."""
        if args.reset_db:
            return self._run_make("reset-db")
        elif args.duplicates:
            return self._run_make("cleanup-duplicates")
        else:
            # Default: run both clean operations
            return self._run_make("clean")
            
    def lint(self, args: argparse.Namespace) -> CommandResult:
        """Lint code command."""
        make_args = []
        
        if args.python:
            make_args.append("lint-python")
        elif args.typescript:
            make_args.append("lint-typescript")
        elif args.shell:
            make_args.append("shellcheck")
        else:
            # Default: run all linters
            make_args.append("lint")
            
        return self._run_make("lint", make_args)
        
    def format(self, args: argparse.Namespace) -> CommandResult:
        """Format code command."""
        make_args = []
        
        if args.python:
            make_args.append("format-python")
        elif args.typescript:
            make_args.append("format-typescript")
        else:
            # Default: format all
            make_args.append("format")
            
        return self._run_make("format", make_args)
        
    def test(self, args: argparse.Namespace) -> CommandResult:
        """Run tests command."""
        if args.coverage:
            return self._run_make("test-coverage")
        else:
            return self._run_make("test")
            
    def config(self, args: argparse.Namespace) -> CommandResult:
        """Configuration management command."""
        if args.backup:
            return self._run_make("config-backup")
        elif args.restore:
            return self._run_make("config-restore")
        elif args.install:
            return self._run_make("config-install")
        elif args.list:
            return self._run_make("config-list")
        elif args.cleanup:
            return self._run_make("config-cleanup")
        else:
            return self._run_make("validate-config")
            
    def help(self, args: argparse.Namespace) -> CommandResult:
        """Enhanced help command."""
        help_args = []
        
        if args.topics:
            help_args.append("help-topics")
        elif args.examples:
            help_args.append("help-examples")
        elif args.topic:
            # Contextual help for specific topic
            return self._show_topic_help(args.topic)
        else:
            help_args.append("help")
            
        return self._run_make("help", help_args)
        
    def _show_topic_help(self, topic: str) -> CommandResult:
        """Show contextual help for specific topic."""
        help_content = {
            "setup": """
🔧 Setup Command

Interactive configuration wizard for MCP Gateway.

Usage:
  make setup                    # Run interactive setup
  make setup --quick            # Quick setup with defaults
  make setup --reconfigure      # Reconfigure existing setup

Features:
• Environment configuration
• Authentication setup
• IDE integration
• Service management
• Development environment
• Validation and testing

Examples:
  make setup                    # Full interactive setup
  make setup --quick            # Quick setup with defaults
  make setup --reconfigure      # Update existing configuration
            """,
            
            "auth": """
🔑 Authentication Command

Manage authentication and security settings.

Usage:
  make auth                     # Generate JWT token
  make auth --generate          # Generate secrets
  make auth --check             # Check configuration
  make auth --refresh           # Refresh JWT token

Features:
• JWT token generation
• Secret key management
• Configuration validation
• Token refresh

Examples:
  make auth --generate          # Generate new secrets
  make auth --check             # Validate current config
  make auth --refresh           # Refresh JWT token
            """,
            
            "ide": """
💻 IDE Setup Command

Configure IDE integration for MCP Gateway.

Usage:
  make ide-setup IDE=<cursor|windsurf|vscode|claude|all>

Supported IDEs:
• Cursor - AI-powered IDE
• Windsurf - AI IDE with MCP support
• VSCode - Visual Studio Code
• Claude Desktop - Claude AI desktop app

Actions:
• install (default) - Install configuration
• backup - Backup existing config
• restore - Restore from backup
• status - Check configuration status

Examples:
  make ide-setup IDE=cursor                    # Install Cursor config
  make ide-setup IDE=all                       # Install all IDE configs
  make ide-setup IDE=windsurf ACTION=backup     # Backup Windsurf config
  make ide-setup IDE=vscode ACTION=status       # Check VS Code status
            """,
            
            "status": """
📊 Status Command

Check system status and health.

Usage:
  make status                   # Basic status
  make status --detailed        # Detailed status
  make status --json            # JSON format output

Information shown:
• Service health
• Active connections
• Resource usage
• Error status
• Performance metrics

Examples:
  make status                   # Basic status overview
  make status --detailed        # Detailed system information
  make status --json            # Machine-readable JSON output
            """,
            
            "troubleshooting": """
🔧 Troubleshooting

Common issues and solutions:

Database Issues:
  make reset-db                 # Reset corrupted database
  make clean                    # Clean up and restart

Authentication Issues:
  make auth --generate          # Regenerate secrets
  make auth --check             # Validate configuration

Service Issues:
  make stop && make start       # Restart services
  make status --detailed        # Check detailed status

Configuration Issues:
  make validate-config           # Validate configuration
  make setup --reconfigure      # Reconfigure setup

Get Help:
  make help                     # Show all commands
  make help --topics            # List help topics
  make help --examples          # Show usage examples
            """
        }
        
        content = help_content.get(topic.lower(), f"❌ Unknown topic: {topic}")
        
        return CommandResult(
            success=True,
            output=content,
            error=""
        )


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        description="Enhanced MCP Gateway Command Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s setup                    # Run interactive setup
  %(prog)s auth --generate          # Generate secrets
  %(prog)s start --gateway-only     # Start only gateway
  %(prog)s status --detailed        # Show detailed status
  %(prog)s lint --python             # Lint Python code only
  %(prog)s help setup                # Show setup help

For more help:
  %(prog)s help --topics            # List help topics
  %(prog)s help --examples          # Show usage examples
        """
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Interactive configuration wizard"
    )
    setup_parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick setup with default values"
    )
    setup_parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="Reconfigure existing setup"
    )
    
    # Auth command
    auth_parser = subparsers.add_parser(
        "auth",
        help="Authentication management"
    )
    auth_group = auth_parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        "--generate",
        action="store_true",
        help="Generate secrets"
    )
    auth_group.add_argument(
        "--check",
        action="store_true",
        help="Check configuration"
    )
    auth_group.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh JWT token"
    )
    
    # Start command
    start_parser = subparsers.add_parser(
        "start",
        help="Start services"
    )
    start_parser.add_argument(
        "--gateway-only",
        action="store_true",
        help="Start only gateway service"
    )
    
    # Stop command
    subparsers.add_parser(
        "stop",
        help="Stop services"
    )
    
    # Register command
    register_parser = subparsers.add_parser(
        "register",
        help="Register virtual servers"
    )
    register_parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for services to be ready"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="System status"
    )
    status_group = status_parser.add_mutually_exclusive_group()
    status_group.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed status"
    )
    status_group.add_argument(
        "--json",
        action="store_true",
        help="JSON format output"
    )
    
    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List resources"
    )
    list_group = list_parser.add_mutually_exclusive_group()
    list_group.add_argument(
        "--servers",
        action="store_true",
        help="List virtual servers"
    )
    list_group.add_argument(
        "--prompts",
        action="store_true",
        help="List available prompts"
    )
    
    # Clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean up system"
    )
    clean_group = clean_parser.add_mutually_exclusive_group()
    clean_group.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset database"
    )
    clean_group.add_argument(
        "--duplicates",
        action="store_true",
        help="Clean duplicate servers"
    )
    
    # Lint command
    lint_parser = subparsers.add_parser(
        "lint",
        help="Run code linters"
    )
    lint_group = lint_parser.add_mutually_exclusive_group()
    lint_group.add_argument(
        "--python",
        action="store_true",
        help="Lint Python code only"
    )
    lint_group.add_argument(
        "--typescript",
        action="store_true",
        help="Lint TypeScript code only"
    )
    lint_group.add_argument(
        "--shell",
        action="store_true",
        help="Lint shell scripts only"
    )
    
    # Format command
    format_parser = subparsers.add_parser(
        "format",
        help="Format code"
    )
    format_group = format_parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--python",
        action="store_true",
        help="Format Python code only"
    )
    format_group.add_argument(
        "--typescript",
        action="store_true",
        help="Format TypeScript code only"
    )
    
    # Test command
    test_parser = subparsers.add_parser(
        "test",
        help="Run tests"
    )
    test_parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration management"
    )
    config_group = config_parser.add_mutually_exclusive_group()
    config_group.add_argument(
        "--backup",
        action="store_true",
        help="Backup configuration"
    )
    config_group.add_argument(
        "--restore",
        action="store_true",
        help="Restore configuration"
    )
    config_group.add_argument(
        "--install",
        action="store_true",
        help="Install configuration"
    )
    config_group.add_argument(
        "--list",
        action="store_true",
        help="List configurations"
    )
    config_group.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old configurations"
    )
    
    # Help command
    help_parser = subparsers.add_parser(
        "help",
        help="Show help information"
    )
    help_group = help_parser.add_mutually_exclusive_group()
    help_group.add_argument(
        "--topics",
        action="store_true",
        help="List help topics"
    )
    help_group.add_argument(
        "--examples",
        action="store_true",
        help="Show usage examples"
    )
    help_group.add_argument(
        "--topic",
        help="Show help for specific topic"
    )
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    manager = CommandManager()
    
    # Map commands to methods
    command_map = {
        "setup": manager.setup,
        "auth": manager.auth,
        "start": manager.start,
        "stop": manager.stop,
        "register": manager.register,
        "status": manager.status,
        "list": manager.list,
        "clean": manager.clean,
        "lint": manager.lint,
        "format": manager.format,
        "test": manager.test,
        "config": manager.config,
        "help": manager.help,
    }
    
    if args.command not in command_map:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)
        
    # Execute command
    try:
        result = command_map[args.command](args)
        
        if result.success:
            if result.output:
                print(result.output)
            sys.exit(0)
        else:
            if result.error:
                print(f"❌ Error: {result.error}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Command cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
