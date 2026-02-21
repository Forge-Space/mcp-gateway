#!/usr/bin/env python3

"""
Enterprise-Grade Features for MCP Gateway
Implements advanced enterprise features like audit logging, compliance, and advanced security
"""

import json
import time
import subprocess
import sys
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
import sqlite3
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AuditEvent:
    """Container for audit events"""
    timestamp: datetime
    event_type: str
    user_id: str
    service_name: str
    action: str
    resource: str
    details: Dict[str, any]
    ip_address: str
    user_agent: str
    success: bool

@dataclass
class ComplianceCheck:
    """Container for compliance check results"""
    timestamp: datetime
    check_type: str
    category: str
    status: str  # compliant, non_compliant, warning
    description: str
    details: Dict[str, any]
    recommendations: List[str]

class EnterpriseFeatures:
    """Enterprise-grade features implementation"""

    def __init__(self, data_dir: str = "/tmp/mcp-gateway-enterprise"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Database setup
        self.db_path = self.data_dir / "audit.db"
        self._init_database()

        # Configuration
        self.audit_retention_days = 90
        self.compliance_standards = {
            'SOC2': True,
            'GDPR': True,
            'HIPAA': False,
            'PCI_DSS': False
        }

        # Security configuration
        self.encryption_key = os.getenv('ENCRYPTION_KEY', 'default-encryption-key-32-chars')
        self.session_timeout = 3600  # 1 hour

        # Load configuration
        self._load_configuration()

    def _init_database(self):
        """Initialize SQLite database for audit logging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create audit events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    service_name TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN NOT NULL,
                    signature TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create compliance checks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    check_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    details TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_service ON audit_events(service_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_compliance_timestamp ON compliance_checks(timestamp)')

            conn.commit()
            conn.close()

            logger.info("Initialized enterprise database")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _load_configuration(self):
        """Load enterprise configuration"""
        config_file = self.data_dir / "config.json"

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.audit_retention_days = config.get('audit_retention_days', 90)
                    self.compliance_standards = config.get('compliance_standards', self.compliance_standards)
                    self.encryption_key = config.get('encryption_key', self.encryption_key)
                    self.session_timeout = config.get('session_timeout', self.session_timeout)

            except Exception as e:
                logger.warning(f"Could not load configuration: {e}")

    def log_audit_event(self, event_type: str, user_id: str, service_name: str,
                        action: str, resource: str, details: Dict[str, any] = None,
                        ip_address: str = None, user_agent: str = None, success: bool = True):
        """Log an audit event"""
        try:
            # Generate digital signature
            signature = self._generate_signature(event_type, user_id, service_name, action, resource)

            # Encrypt sensitive details
            encrypted_details = self._encrypt_data(json.dumps(details) if details else '{}')

            # Insert into database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO audit_events
                (timestamp, event_type, user_id, service_name, action, resource, details,
                 ip_address, user_agent, success, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                event_type,
                user_id,
                service_name,
                action,
                resource,
                encrypted_details,
                ip_address or 'unknown',
                user_agent or 'unknown',
                success,
                signature
            ))

            conn.commit()
            conn.close()

            logger.info(f"Logged audit event: {event_type} by {user_id} for {service_name}")

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def _generate_signature(self, event_type: str, user_id: str, service_name: str,
                          action: str, resource: str) -> str:
        """Generate digital signature for audit event"""
        # Create signature string
        signature_string = f"{event_type}|{user_id}|{service_name}|{action}|{resource}|{datetime.now().isoformat()}"

        # Generate HMAC signature
        signature = hmac.newhash(
            self.encryption_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        # Simple encryption (in production, use proper encryption libraries)
        # This is a placeholder implementation
        encoded = data.encode('utf-8').hex()
        return encoded

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        # Simple decryption (in production, use proper encryption libraries)
        # This is a placeholder implementation
        try:
            return bytes.fromhex(encrypted_data).decode('utf-8')
        except:
            return ""

    def run_compliance_check(self, check_type: str = None) -> List[ComplianceCheck]:
        """Run compliance checks"""
        checks = []

        if check_type:
            # Run specific check
            if check_type == 'security':
                checks.extend(self._check_security_compliance())
            elif check_type == 'privacy':
                checks.extend(self._check_privacy_compliance())
            elif check_type == 'access':
                checks.extend(self._check_access_compliance())
            elif check_type == 'data_protection':
                checks.extend(self._check_data_protection_compliance())
        else:
            # Run all compliance checks
            checks.extend(self._check_security_compliance())
            checks.extend(self._check_privacy_compliance())
            checks.extend(self._check_access_compliance())
            checks.extend(self._check_data_protection_compliance())
            checks.extend(self._check_operational_compliance())

        # Save compliance check results
        self._save_compliance_checks(checks)

        return checks

    def _check_security_compliance(self) -> List[ComplianceCheck]:
        """Check security compliance"""
        checks = []

        # Check for strong passwords
        checks.append(self._check_password_security())

        # Check for SSL/TLS configuration
        checks.append(self._check_ssl_configuration())

        # Check for container security
        checks.append(self._check_container_security())

        # Check for network security
        checks.append(self._check_network_security())

        # Check for authentication mechanisms
        checks.append(self._check_authentication_security())

        return checks

    def _check_password_security(self) -> ComplianceCheck:
        """Check password security compliance"""
        details = {}
        recommendations = []

        try:
            env_file = Path(".env.production")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    lines = f.readlines()

                weak_passwords = 0
                missing_passwords = 0
                short_passwords = 0

                for line in lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if 'PASSWORD' in key or 'SECRET' in key:
                            if not value.strip():
                                missing_passwords += 1
                            elif len(value.strip()) < 32:
                                short_passwords += 1
                            elif 'your-' in value or 'example' in value or 'test' in value:
                                weak_passwords += 1

                status = 'non_compliant' if (weak_passwords > 0 or missing_passwords > 0 or short_passwords > 0) else 'compliant'

                details = {
                    'weak_passwords': weak_passwords,
                    'missing_passwords': missing_passwords,
                    'short_passwords': short_passwords
                }

                if weak_passwords > 0:
                    recommendations.append("Replace weak/default passwords")
                if missing_passwords > 0:
                    recommendations.append("Configure missing passwords")
                if short_passwords > 0:
                    recommendations.append("Use passwords with at least 32 characters")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check password security"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='password_security',
            category='security',
            status=status,
            description="Password security compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_ssl_configuration(self) -> ComplianceCheck:
        """Check SSL/TLS configuration compliance"""
        details = {}
        recommendations = []

        try:
            env_file = Path(".env.production")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()

                ssl_configured = 'SSL_CERT_PATH' in content and 'SSL_KEY_PATH' in content
                cert_exists = False
                key_exists = False

                if ssl_configured:
                    cert_path = None
                    key_path = None

                    for line in content.split('\n'):
                        if 'SSL_CERT_PATH=' in line:
                            cert_path = line.split('=', 1)[1].strip()
                        elif 'SSL_KEY_PATH=' in line:
                            key_path = line.split('=', 1)[1].strip()

                    if cert_path and Path(cert_path).exists():
                        cert_exists = True

                    if key_path and Path(key_path).exists():
                        key_exists = True

                status = 'compliant' if ssl_configured and cert_exists and key_exists else 'non_compliant'

                details = {
                    'ssl_configured': ssl_configured,
                    'cert_exists': cert_exists,
                    'key_exists': key_exists
                }

                if not ssl_configured:
                    recommendations.append("Configure SSL/TLS certificates")
                if not cert_exists:
                    recommendations.append("Install SSL certificate file")
                if not key_exists:
                    recommendations.append("Install SSL private key file")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check SSL configuration"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='ssl_configuration',
            category='security',
            status=status,
            description="SSL/TLS configuration compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_container_security(self) -> ComplianceCheck:
        """Check container security compliance"""
        details = {}
        recommendations = []
        status = 'warning'  # Default status

        try:
            # Check if containers are running as root
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}\t{{.User}}'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                root_containers = 0
                total_containers = 0

                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            total_containers += 1
                            if parts[1] == 'root' or parts[1] == '0':
                                root_containers += 1

                status = 'non_compliant' if root_containers > 0 else 'compliant'

                details = {
                    'root_containers': root_containers,
                    'total_containers': total_containers
                }

                if root_containers > 0:
                    recommendations.append("Configure containers to run as non-root users")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check container security"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='container_security',
            category='security',
            status=status,
            description="Container security compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_network_security(self) -> List[ComplianceCheck]:
        """Check network security compliance"""
        details = {}
        recommendations = []

        try:
            # Check for exposed ports
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Ports}}'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                exposed_ports = 0
                total_ports = 0

                for line in lines:
                    if line.strip() and '->' in line:
                        total_ports += 1
                        if '0.0.0.0:' not in line:  # Not bound to localhost
                            exposed_ports += 1

                status = 'warning' if exposed_ports > 0 else 'compliant'

                details = {
                    'exposed_ports': exposed_ports,
                    'total_ports': total_ports
                }

                if exposed_ports > 0:
                    recommendations.append("Review exposed ports and limit to necessary services")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check network security"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='network_security',
            category='security',
            status=status,
            description="Network security compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_authentication_security(self) -> List[Compliance]:
        """Check authentication security compliance"""
        details = {}
        recommendations = []

        try:
            env_file = Path(".env.production")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()

                jwt_configured = 'JWT_SECRET' in content
                session_timeout_configured = 'SESSION_TIMEOUT' in content

                status = 'compliant' if jwt_configured and session_timeout_configured else 'non_compliant'

                details = {
                    'jwt_configured': jwt_configured,
                    'session_timeout_configured': session_timeout_configured
                }

                if not jwt_configured:
                    recommendations.append("Configure JWT authentication")
                if not session_timeout_configured:
                    recommendations.append("Configure session timeout")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check authentication security"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='authentication_security',
            category='security',
            status=status,
            description="Authentication security compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_privacy_compliance(self) -> List[ComplianceCheck]:
        """Check privacy compliance (GDPR)"""
        checks = []

        if self.compliance_standards.get('GDPR', False):
            return checks

        # Check for data minimization
        checks.append(self._check_data_minimization())

        # Check for consent management
        checks.append(self._check_consent_management())

        # Check for data retention policies
        checks.append(self._check_data_retention())

        # Check for data subject rights
        checks.append(self._check_data_subject_rights())

        return checks

    def _check_data_minimization(self) -> ComplianceCheck:
        """Check data minimization compliance"""
        details = {}
        recommendations = []

        try:
            # Check for unnecessary data collection
            env_file = Path(".env.production")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()

                # Check for debug logging in production
                debug_enabled = 'DEBUG=true' in content

                status = 'non_compliant' if debug_enabled else 'compliant'

                details = {'debug_enabled': debug_enabled}

                if debug_enabled:
                    recommendations.append("Disable debug logging in production")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check data minimization"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='data_minimization',
            category='privacy',
            status=status,
            description="Data minimization compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_consent_management(self) -> ComplianceCheck:
        """Check consent management compliance"""
        details = {}
        recommendations = []

        # Mock implementation - in production would check actual consent mechanisms
        status = 'warning'
        details = {'status': 'not_implemented'}
        recommendations = ["Implement consent management system"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='consent_management',
            category='privacy',
            status=status,
            description="Consent management compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_data_retention(self) -> ComplianceCheck:
        """Check data retention compliance"""
        details = {}
        recommendations = []

        try:
            # Check audit log retention
            log_files = list(Path("./logs").glob("*.log"))

            old_logs = 0
            for log_file in log_files:
                file_age = (datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)).days
                if file_age > self.audit_retention_days:
                    old_logs += 1

            status = 'non_compliant' if old_logs > 0 else 'compliant'

            details = {'old_logs': old_logs, 'retention_days': self.audit_retention_days}

            if old_logs > 0:
                recommendations.append(f"Remove logs older than {self.audit_retention_days} days")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check data retention"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='data_retention',
            category='privacy',
            status=status,
            description="Data retention compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_data_subject_rights(self) -> ComplianceCheck:
        """Check data subject rights compliance"""
        details = {}
        recommendations = []

        # Mock implementation - in production would check actual data subject rights
        status = 'warning'
        details = {'status': 'not_implemented'}
        recommendations = ["Implement data subject rights management"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='data_subject_rights',
            category='privacy',
            status=status,
            description="Data subject rights compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_access_compliance(self) -> List[Compliance]:
        """Check access control compliance"""
        checks = []

        # Check for role-based access control
        checks.append(self._check_rbac_compliance())

        # Check for principle of least privilege
        checks.append(self._check_polp_compliance())

        # Check for access logging
        checks.append(self._check_access_logging())

        return checks

    def _check_rbac_compliance(self) -> ComplianceCheck:
        """Check role-based access control compliance"""
        details = {}
        recommendations = []

        # Mock implementation - in production would check actual RBAC system
        status = 'warning'
        details = {'status': 'not_implemented'}
        recommendations = ["Implement role-based access control system"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='rbac_compliance',
            category='access',
            status=status,
            description="Role-based access control compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_polp_compliance(self) -> ComplianceCheck:
        """Check principle of least privilege compliance"""
        details = {}
        recommendations = []

        # Mock implementation - in production would check actual privilege levels
        status = 'warning'
        details = {'status': 'not_implemented'}
        recommendations = ["Implement principle of least privilege enforcement"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='polp_compliance',
            category='access',
            status=status,
            description="Principle of least privilege compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_access_logging(self) -> ComplianceCheck:
        """Check access logging compliance"""
        details = {}
        recommendations = []

        try:
            # Check if audit logging is enabled
            env_file = Path(".env.production")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()

                audit_logging_enabled = 'AUDIT_LOGGING=true' in content

                status = 'compliant' if audit_logging_enabled else 'non_compliant'

                details = {'audit_logging_enabled': audit_logging_enabled}

                if not audit_logging_enabled:
                    recommendations.append("Enable audit logging")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check access logging"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='access_logging',
            category='access',
            status=status,
            description="Access logging compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_data_protection_compliance(self) -> List[Compliance]:
        """Check data protection compliance"""
        checks = []

        # Check for encryption at rest
        checks.append(self._check_encryption_at_rest())

        # Check for data backup
        checks.append(self._check_data_backup())

        # Check for data integrity
        checks.append(self._check_data_integrity())

        return checks

    def _check_encryption_at_rest(self) -> ComplianceCheck:
        """Check encryption at rest compliance"""
        details = {}
        recommendations = []

        # Mock implementation - in production would check actual encryption
        status = 'warning'
        details = {'status': 'not_implemented'}
        recommendations = ["Implement encryption at rest for sensitive data"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='encryption_at_rest',
            category='data_protection',
            status=status,
            description="Encryption at rest compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_data_backup(self) -> ComplianceCheck:
        """Check data backup compliance"""
        details = {}
        recommendations = []

        try:
            # Check for backup directory
            backup_dir = Path("./backups")
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*"))

                recent_backups = 0
                for backup_file in backup_files:
                    file_age = (datetime.now() - datetime.fromtimestamp(backup_file.stat().st_mtime)).days
                    if file_age <= 7:  # Backups within last week
                        recent_backups += 1

                status = 'compliant' if recent_backups >= 1 else 'non_compliant'

                details = {'recent_backups': recent_backups, 'total_backups': len(backup_files)}

                if recent_backups < 1:
                    recommendations.append("Ensure regular backups are performed")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check data backup"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='data_backup',
            category='data_protection',
            status=status,
            description="Data backup compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_data_integrity(self) -> ComplianceCheck:
        """Check data integrity compliance"""
        details = {}
        recommendations = []

        # Mock implementation - in production would check data integrity
        status = 'warning'
        details = {'status': 'not_implemented'}
        recommendations = ["Implement data integrity checks"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='data_integrity',
            category='data_protection',
            status=status,
            description="Data integrity compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_operational_compliance(self) -> List[Compliance]:
        """Check operational compliance"""
        checks = []

        # Check for monitoring
        checks.append(self._check_monitoring_compliance())

        # Check for incident response
        checks.append(self._check_incident_response_compliance())

        # Check for disaster recovery
        checks.append(self._check_disaster_recovery_compliance())

        return checks

    def _check_monitoring_compliance(self) -> ComplianceCheck:
        """Check monitoring compliance"""
        details = {}
        recommendations = []

        try:
            # Check if monitoring is configured
            monitoring_configured = Path("./config/prometheus").exists() and Path("./config/grafana").exists()

            status = 'compliant' if monitoring_configured else 'non_compliant'

            details = {'monitoring_configured': monitoring_configured}

            if not monitoring_configured:
                recommendations.append("Configure monitoring and alerting")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check monitoring compliance"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='monitoring_compliance',
            category='operational',
            status=status,
            description="Monitoring compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_incident_response_compliance(self) -> ComplianceCheck:
        """Check incident response compliance"""
        details = {}
        recommendations = []

        # Mock implementation - in production would check incident response procedures
        status = 'warning'
        details = {'status': 'not_implemented'}
        recommendations = ["Implement incident response procedures"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='incident_response_compliance',
            category='operational',
            status=status,
            description="Incident response compliance check",
            details=details,
            recommendations=recommendations
        )

    def _check_disaster_recovery_compliance(self) -> ComplianceCheck:
        """Check disaster recovery compliance"""
        details = {}
        recommendations = []

        try:
            # Check for backup directory
            backup_dir = Path("./backups")
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*"))

                status = 'compliant' if len(backup_files) >= 1 else 'non_compliant'

                details = {'backup_files': len(backup_files)}

                if len(backup_files) < 1:
                    recommendations.append("Implement disaster recovery procedures")

        except Exception as e:
            status = 'warning'
            details = {'error': str(e)}
            recommendations = ["Unable to check disaster recovery compliance"]

        return ComplianceCheck(
            timestamp=datetime.now(),
            check_type='disaster_recovery_compliance',
            category='operational',
            status=status,
            description="Disaster recovery compliance check",
            details=details,
            recommendations=recommendations
        )

    def _save_compliance_checks(self, checks: List[ComplianceCheck]):
        """Save compliance check results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for check in checks:
                cursor.execute('''
                    INSERT INTO compliance_checks
                    (timestamp, check_type, category, status, description, details, recommendations, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    check.timestamp.isoformat(),
                    check.check_type,
                    check.category,
                    check.status,
                    check.description,
                    json.dumps(check.details),
                    json.dumps(check.recommendations),
                    datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            logger.info(f"Saved {len(checks)} compliance checks")

        except Exception as e:
            logger.error(f"Failed to save compliance checks: {e}")

    def get_audit_trail(self, user_id: str = None, service_name: str = None,
                        start_time: datetime = None, end_time: datetime = None,
                        limit: int = 100) -> List[Dict[str, any]]:
        """Get audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build query
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if service_name:
                query += " AND service_name = ?"
                params.append(service_name)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'event_type': row[2],
                    'user_id': row[3],
                    'service_name': row[4],
                    'action': row[5],
                    'resource': row[6],
                    'details': row[7],
                    'ip_address': row[8],
                    'user_agent': row[9],
                    'success': row[10],
                    'signature': row[11]
                })

            conn.close()

            # Decrypt details
            for result in results:
                if result['details']:
                    try:
                        result['details'] = self._decrypt_data(result['details'])
                    except:
                        result['details'] = {}

            return results

        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return []

    def get_compliance_report(self) -> Dict[str, any]:
        """Get comprehensive compliance report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get compliance check statistics
            cursor.execute('''
                SELECT
                    category,
                    status,
                    COUNT(*) as count
                FROM compliance_checks
                GROUP BY category, status
                ORDER BY category, status
            ''')

            stats_rows = cursor.fetchall()

            # Get recent compliance checks
            cursor.execute('''
                SELECT * FROM compliance_checks
                ORDER BY timestamp DESC
                LIMIT 50
            ''')

            recent_checks = cursor.fetchall()

            conn.close()

            # Generate report
            report = {
                'timestamp': datetime.now().isoformat(),
                'compliance_standards': self.compliance_standards,
                'statistics': {
                    category: [row[0] for row in stats_rows],
                    status: [row[1] for row in stats_rows],
                    count: [row[2] for row in stats_rows]
                },
                'recent_checks': [
                    {
                        'id': row[0],
                        'timestamp': row[1],
                        'check_type': row[2],
                        'category': row[3],
                        'status': row[4],
                        'description': row[5],
                        'recommendations': json.loads(row[6]) if row[6] else []
                    } for row in recent_checks
                ]
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {}

    def cleanup_old_data(self):
        """Clean up old audit data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Delete old audit events
            cutoff_date = datetime.now() - timedelta(days=self.audit_retention_days)
            cursor.execute("DELETE FROM audit_events WHERE timestamp < ?", (cutoff_date.isoformat(),))

            # Delete old compliance checks
            cursor.execute("DELETE FROM compliance_checks WHERE timestamp < ?", (cutoff_date.isoformat(),))

            conn.commit()
            conn.close()

            logger.info(f"Cleaned up data older than {self.audit_retention_days} days")

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Enterprise-Grade Features for MCP Gateway')
    parser.add_argument('--audit', action='store_true', help='Log audit event')
    parser.add_argument('--check-compliance', action='store_true', help='Run compliance checks')
    parser.add_argument('--check-type', help='Specific compliance check type')
    parser.add_argument('--audit-trail', action='store_true', help='Get audit trail')
    def main():
        parser.add_argument('--user-id', help='User ID for audit trail')
        parser.add_argument('--service', help='Service name for audit trail')
        parser.add_argument('--report', action='store_true', help='Generate compliance report')
        parser.add_argument('--cleanup', action='store_true', help='Clean up old data')

    args = parser.parse_args()

    enterprise = EnterpriseFeatures()

    if args.audit:
        enterprise.log_audit_event(
            event_type='manual_test',
            user_id=args.user_id or 'system',
            service_name=args.service or 'system',
            action='test',
            resource='test_resource',
            details={'test': True},
            success=True
        )
        print("Audit event logged")

    elif args.check_compliance:
        if args.check_type:
            checks = enterprise.run_compliance_check(args.check_type)
            print(f"Compliance check completed: {len(checks)} checks")
            for check in checks:
                print(f"- {check.check_type}: {check.status} ({check.category})")
                if check.recommendations:
                    print(f"  Recommendations: {', '.join(check.recommendations)}")
        else:
            checks = enterprise.run_compliance_check()
            print(f"Compliance check completed: {len(checks)} checks")

            # Group by category
            by_category = {}
            for check in checks:
                if check.category not in by_category:
                    by_category[check.category] = []
                by_category[check.category].append(check)

            for category, category_checks in by_category.items():
                compliant = len([c for c in category_checks if c.status == 'compliant'])
                total = len(category_checks)
                print(f"{category}: {compliant}/{total} compliant")

    elif args.audit_trail:
        trail = enterprise.get_audit_trail(
            user_id=args.user_id,
            service_name=args.service,
            limit=int(args.limit) if args.limit else 100
        )
        print(f"Audit trail ({len(trail)} entries):")
        for entry in trail:
            print(f"{entry['timestamp']} - {entry['event_type']} - {entry['user_id']} - {entry['service_name']} - {entry['action']}")

    elif args.report:
        report = enterprise.get_compliance_report()
        print(json.dumps(report, indent=2))

    elif args.cleanup:
        enterprise.cleanup_old_data()
        print("Cleanup completed")

    else:
        # Default: run full compliance check
        checks = enterprise.run_compliance_check()
        print(f"Enterprise compliance check completed: {len(checks)} checks")

        # Group by category
        by_category = {}
        for check in checks:
            if check.category not in by_category:
                by_category[check.category] = []
            by_category[check.category].append(check)

        for category, category_checks in by_category.items():
            compliant = len([c for c in category_checks if c.status == 'compliant'])
            total = len(category_checks)
            print(f"{category}: {compliant}/{total} compliant")

            if compliant < total:
                print(f"  Issues in {category}:")
                for check in category_checks:
                    if check.status != 'compliant':
                        print(f"    - {check.check_type}: {check.description}")
                        if check.recommendations:
                            print(f"      Recommendations: {', '.join(check.recommendations)}")

if __name__ == '__main__':
    main()
