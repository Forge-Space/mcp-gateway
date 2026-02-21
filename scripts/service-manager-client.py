#!/usr/bin/env python3
"""
Service Manager Client for Forge MCP Gateway

A command-line tool to interact with the dynamic service manager.
"""

import argparse
import sys
from typing import Dict, List

import requests


class ServiceManagerClient:
    """Client for interacting with the Service Manager API."""

    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to the service manager API."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

        except requests.exceptions.ConnectionError:
            print(f"Error: Cannot connect to service manager at {self.base_url}")
            print("Make sure the service manager is running.")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            if e.response.content:
                try:
                    error_data = e.response.json()
                    print(f"Details: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"Details: {e.response.content.decode()}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            sys.exit(1)

    def health(self) -> Dict:
        """Get service manager health status."""
        return self._request('GET', '/health')

    def list_services(self) -> List[Dict]:
        """List all services and their status."""
        return self._request('GET', '/services')

    def get_service(self, service_name: str) -> Dict:
        """Get status of a specific service."""
        return self._request('GET', f'/services/{service_name}')

    def start_service(self, service_name: str) -> Dict:
        """Start a service."""
        return self._request('POST', f'/services/{service_name}/start')

    def stop_service(self, service_name: str) -> Dict:
        """Stop a service."""
        return self._request('POST', f'/services/{service_name}/stop')

    def sleep_service(self, service_name: str) -> Dict:
        """Put a service to sleep."""
        return self._request('POST', f'/services/{service_name}/sleep')

    def wake_service(self, service_name: str) -> Dict:
        """Wake a service from sleep."""
        return self._request('POST', f'/services/{service_name}/wake')

    def auto_scale(self) -> Dict:
        """Trigger auto-scaling."""
        return self._request('POST', '/services/auto-scale')


def format_service_status(service: Dict) -> str:
    """Format service status for display."""
    status = service.get('status', 'unknown')
    name = service.get('name', 'unknown')
    port = service.get('port')
    container_id = service.get('container_id', 'N/A')
    last_accessed = service.get('last_accessed')
    error_message = service.get('error_message')

    # Status colors (for terminal output)
    status_colors = {
        'running': '\033[92m',    # Green
        'stopped': '\033[91m',    # Red
        'starting': '\033[93m',   # Yellow
        'stopping': '\033[93m',   # Yellow
        'sleeping': '\033[94m',   # Blue
        'waking': '\033[93m',     # Yellow
        'error': '\033[91m',      # Red
    }

    color = status_colors.get(status, '')
    reset = '\033[0m'

    output = f"{color}{name}{reset}: {color}{status}{reset}"

    if port:
        output += f" (port: {port})"

    if container_id and container_id != 'N/A':
        output += f" [id: {container_id[:12]}...]"

    if last_accessed:
        output += f" [last: {last_accessed}]"

    if error_message:
        output += f" [error: {error_message}]"

    return output


def cmd_health(args):
    """Show service manager health."""
    client = ServiceManagerClient(args.url)
    health = client.health()

    print("Service Manager Health:")
    print(f"  Status: {health.get('status', 'unknown')}")
    print(f"  Docker Connection: {health.get('docker_connection', 'unknown')}")
    print(f"  Services Running: {health.get('services_running', '0')}")
    print(f"  Services Total: {health.get('services_total', '0')}")


def cmd_list(args):
    """List all services."""
    client = ServiceManagerClient(args.url)
    services = client.list_services()

    if not services:
        print("No services found.")
        return

    print("Services:")
    for service in services:
        print(f"  {format_service_status(service)}")

    # Summary
    running = sum(1 for s in services if s.get('status') == 'running')
    total = len(services)
    print(f"\nSummary: {running}/{total} services running")


def cmd_status(args):
    """Show status of a specific service."""
    client = ServiceManagerClient(args.url)
    service = client.get_service(args.service)

    print(f"Service Status: {args.service}")
    print(f"  Status: {service.get('status', 'unknown')}")
    print(f"  Port: {service.get('port', 'N/A')}")
    print(f"  Container ID: {service.get('container_id', 'N/A')}")
    print(f"  Last Accessed: {service.get('last_accessed', 'N/A')}")

    if service.get('error_message'):
        print(f"  Error: {service.get('error_message')}")

    if service.get('resource_usage'):
        print("  Resource Usage:")
        for resource, usage in service.get('resource_usage', {}).items():
            print(f"    {resource}: {usage}")


def cmd_start(args):
    """Start a service."""
    client = ServiceManagerClient(args.url)

    print(f"Starting service: {args.service}")
    service = client.start_service(args.service)

    print(f"Service {args.service} started successfully!")
    print(f"  Status: {service.get('status')}")
    print(f"  Port: {service.get('port')}")
    print(f"  Container ID: {service.get('container_id')}")


def cmd_stop(args):
    """Stop a service."""
    client = ServiceManagerClient(args.url)

    print(f"Stopping service: {args.service}")
    service = client.stop_service(args.service)

    print(f"Service {args.service} stopped successfully!")
    print(f"  Status: {service.get('status')}")


def cmd_sleep(args):
    """Put a service to sleep."""
    client = ServiceManagerClient(args.url)

    print(f"Sleeping service: {args.service}")
    service = client.sleep_service(args.service)

    print(f"Service {args.service} slept successfully!")
    print(f"  Status: {service.get('status')}")
    if service.get('sleep_start_time'):
        print(f"  Sleep started at: {service.get('sleep_start_time')}")


def cmd_wake(args):
    """Wake a service from sleep."""
    client = ServiceManagerClient(args.url)

    print(f"Waking service: {args.service}")
    service = client.wake_service(args.service)

    print(f"Service {args.service} woke successfully!")
    print(f"  Status: {service.get('status')}")
    print(f"  Wake count: {service.get('wake_count', 0)}")
    print(f"  Total sleep time: {service.get('total_sleep_time', 0.0):.1f}s")


def cmd_auto_scale(args):
    """Trigger auto-scaling."""
    client = ServiceManagerClient(args.url)

    print("Triggering auto-scaling...")
    result = client.auto_scale()

    print("Auto-scaling triggered successfully!")
    print(f"  Message: {result.get('message', 'Auto-scaling completed')}")


def cmd_watch(args):
    """Watch services status continuously."""
    import time

    client = ServiceManagerClient(args.url)

    try:
        while True:
            # Clear screen
            print('\033[2J\033[H', end='')

            # Show header
            print(f"Service Manager Status - {args.url}")
            print(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)

            # Show health
            health = client.health()
            print(f"Health: {health.get('status', 'unknown')} | "
                  f"Services: {health.get('services_running', '0')}/{health.get('services_total', '0')}")
            print("-" * 50)

            # Show services
            services = client.list_services()
            for service in services:
                print(f"  {format_service_status(service)}")

            # Show next update time
            print(f"\nNext update in {args.interval} seconds... (Ctrl+C to exit)")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nStopped watching.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Forge MCP Gateway Service Manager Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s health                          # Check service manager health
  %(prog)s list                           # List all services
  %(prog)s status filesystem              # Show filesystem service status
  %(prog)s start filesystem               # Start filesystem service
  %(prog)s stop filesystem                # Stop filesystem service
  %(prog)s sleep filesystem               # Put filesystem service to sleep
  %(prog)s wake filesystem                # Wake filesystem service from sleep
  %(prog)s watch                          # Watch services continuously
  %(prog)s --url http://localhost:9000 list  # Use custom URL
        """
    )

    parser.add_argument(
        '--url',
        default='http://localhost:9000',
        help='Service manager URL (default: http://localhost:9000)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Health command
    health_parser = subparsers.add_parser('health', help='Show service manager health')
    health_parser.set_defaults(func=cmd_health)

    # List command
    list_parser = subparsers.add_parser('list', help='List all services')
    list_parser.set_defaults(func=cmd_list)

    # Status command
    status_parser = subparsers.add_parser('status', help='Show service status')
    status_parser.add_argument('service', help='Service name')
    status_parser.set_defaults(func=cmd_status)

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a service')
    start_parser.add_argument('service', help='Service name')
    start_parser.set_defaults(func=cmd_start)

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop a service')
    stop_parser.add_argument('service', help='Service name')
    stop_parser.set_defaults(func=cmd_stop)

    # Sleep command
    sleep_parser = subparsers.add_parser('sleep', help='Put a service to sleep')
    sleep_parser.add_argument('service', help='Service name')
    sleep_parser.set_defaults(func=cmd_sleep)

    # Wake command
    wake_parser = subparsers.add_parser('wake', help='Wake a service from sleep')
    wake_parser.add_argument('service', help='Service name')
    wake_parser.set_defaults(func=cmd_wake)

    # Auto-scale command
    autoscale_parser = subparsers.add_parser('auto-scale', help='Trigger auto-scaling')
    autoscale_parser.set_defaults(func=cmd_auto_scale)

    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Watch services continuously')
    watch_parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Update interval in seconds (default: 5)'
    )
    watch_parser.set_defaults(func=cmd_watch)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
