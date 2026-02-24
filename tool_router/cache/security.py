"""
Cache Security Module - Phase 2.4 Implementation

This module provides comprehensive security features for the MCP Gateway caching system:
- Encryption and decryption of sensitive data
- Access control and permission management
- GDPR compliance features
- Audit trail functionality
- Security policy management

Key Components:
- CacheEncryption: Fernet-based encryption for sensitive data
- AccessControlManager: Role-based access control with permissions
- GDPRComplianceManager: GDPR compliance features (consent, right to be forgotten)
- RetentionPolicyManager: Data retention and lifecycle management
- CacheSecurityManager: Integrated security manager
"""

import json
import secrets
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from .config import CacheConfig
from .types import (
    AccessLevel,
    AccessRequest,
    AuditEntry,
    CacheEntryMetadata,
    ConsentRecord,
    DataClassification,
    EncryptionError,
    SecurityMetrics,
    SecurityPolicy,
)


class CacheEncryption:
    """Handles encryption and decryption of cache data using Fernet symmetric encryption."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize encryption with configuration."""
        self.config = config or CacheConfig()
        self._encryption_key: str | None = None
        self._fernet: Fernet | None = None
        self._lock = Lock()

        # Set encryption key if available in config
        if self.config.encryption_key:
            self.set_encryption_key(self.config.encryption_key)

    def set_encryption_key(self, key: str | bytes) -> None:
        """Set the encryption key for Fernet encryption."""
        with self._lock:
            if isinstance(key, str):
                key = key.encode()

            try:
                self._fernet = Fernet(key)
                self._encryption_key = key.decode()
            except Exception as e:
                raise EncryptionError(f"Failed to set encryption key: {e}")

    def get_encryption_key(self) -> str | None:
        """Get the current encryption key."""
        return self._encryption_key

    def encrypt(self, data: Any) -> bytes | None:
        """Encrypt data using Fernet encryption."""
        if self._fernet is None:
            raise EncryptionError("Encryption key not set")

        if data is None:
            return None

        try:
            # Serialize data to JSON for consistent encryption
            if isinstance(data, (dict, list, tuple)):
                serialized = json.dumps(data, sort_keys=True).encode()
            elif isinstance(data, str):
                serialized = data.encode()
            elif isinstance(data, bytes):
                serialized = data
            else:
                serialized = str(data).encode()

            encrypted = self._fernet.encrypt(serialized)
            return encrypted

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, encrypted_data: bytes) -> Any:
        """Decrypt data using Fernet encryption."""
        if self._fernet is None:
            raise EncryptionError("Encryption key not set")

        if encrypted_data is None:
            return None

        try:
            decrypted = self._fernet.decrypt(encrypted_data)

            # Try to deserialize as JSON first
            try:
                return json.loads(decrypted.decode())
            except json.JSONDecodeError:
                # Return as string if not valid JSON
                return decrypted.decode()

        except InvalidToken:
            raise EncryptionError("Failed to decrypt data: Invalid token or wrong key")
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt data: {e}")

    def generate_key(self) -> str:
        """Generate a new encryption key."""
        key = Fernet.generate_key()
        return key.decode()

    def rotate_key(self) -> str:
        """Rotate the encryption key and return the new key."""
        new_key = self.generate_key()
        self.set_encryption_key(new_key)
        return new_key


class AccessControlManager:
    """Manages access control policies and permissions for cache operations."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize access control manager."""
        self.config = config or CacheConfig()
        self.policies: dict[str, SecurityPolicy] = {}
        self.access_requests: list[AccessRequest] = []
        self.user_permissions: dict[str, set[AccessLevel]] = defaultdict(set)
        self._lock = Lock()

        # Initialize default policies
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """Initialize default security policies."""
        default_policies = {
            "public_policy": SecurityPolicy(
                policy_id="public_policy",
                name="Public Data Policy",
                description="Default policy for public data",
                classification=DataClassification.PUBLIC,
                retention_days=30,
                encryption_required=False,
                access_controls=[AccessLevel.READ],
                audit_required=True,
                consent_required=False,
                created_at=datetime.now(),
            ),
            "internal_policy": SecurityPolicy(
                policy_id="internal_policy",
                name="Internal Data Policy",
                description="Default policy for internal data",
                classification=DataClassification.INTERNAL,
                retention_days=90,
                encryption_required=False,
                access_controls=[AccessLevel.READ, AccessLevel.WRITE],
                audit_required=True,
                consent_required=False,
                created_at=datetime.now(),
            ),
            "confidential_policy": SecurityPolicy(
                policy_id="confidential_policy",
                name="Confidential Data Policy",
                description="Default policy for confidential data",
                classification=DataClassification.CONFIDENTIAL,
                retention_days=180,
                encryption_required=True,
                access_controls=[
                    AccessLevel.READ,
                    AccessLevel.WRITE,
                    AccessLevel.DELETE,
                ],
                audit_required=True,
                consent_required=True,
                created_at=datetime.now(),
            ),
        }

        for policy_id, policy in default_policies.items():
            self.policies[policy_id] = policy

    def create_policy(self, policy_id: str, policy: SecurityPolicy) -> bool:
        """Create a new security policy."""
        with self._lock:
            if policy_id in self.policies:
                return False

            self.policies[policy_id] = policy
            return True

    def get_policy(self, policy_id: str) -> SecurityPolicy | None:
        """Get a security policy by ID."""
        return self.policies.get(policy_id)

    def list_policies(self) -> dict[str, SecurityPolicy]:
        """List all security policies."""
        return self.policies.copy()

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a security policy."""
        with self._lock:
            if policy_id in self.policies:
                del self.policies[policy_id]
                return True
            return False

    def create_access_request(
        self,
        user_id: str,
        operation: AccessLevel,
        key: str,
        data_classification: DataClassification,
        reason: str = "",
    ) -> int:
        """Create an access request for a cache operation."""
        request = AccessRequest(
            user_id=user_id,
            operation=operation,
            key=key,
            data_classification=data_classification,
            reason=reason,
            expires_at=datetime.now() + timedelta(hours=self.config.access_request_expiry_hours),
        )

        with self._lock:
            request_id = len(self.access_requests)
            self.access_requests.append(request)
            return request_id

    def approve_access_request(self, request_id: int, approved_by: str) -> bool:
        """Approve an access request."""
        with self._lock:
            if 0 <= request_id < len(self.access_requests):
                request = self.access_requests[request_id]
                if not request.approved and not request.expired():
                    request.approved = True
                    request.approved_by = approved_by
                    request.approved_at = datetime.now()

                    # Add to user permissions
                    self.user_permissions[request.user_id].add(request.operation)
                    return True
            return False

    def deny_access_request(self, request_id: int, denied_by: str, reason: str = "") -> bool:
        """Deny an access request."""
        with self._lock:
            if 0 <= request_id < len(self.access_requests):
                request = self.access_requests[request_id]
                if not request.approved and not request.expired():
                    request.approved = False
                    request.approved_by = denied_by
                    # Store denial reason in metadata
                    request.metadata["denied_by"] = denied_by
                    request.metadata["denial_reason"] = reason
                    request.metadata["denied_at"] = datetime.now().isoformat()
                    return True
            return False

    def check_access(
        self,
        user_id: str,
        operation: AccessLevel,
        key: str,
        data_classification: DataClassification,
    ) -> bool:
        """Check if a user has access to perform an operation."""
        # Check if user has the required permission
        if operation in self.user_permissions.get(user_id, set()):
            return True

        # Check if there's an approved request for this specific operation
        with self._lock:
            for request in self.access_requests:
                if (
                    request.user_id == user_id
                    and request.operation == operation
                    and request.key == key
                    and request.data_classification == data_classification
                    and request.approved
                    and not request.expired()
                ):
                    return True

        return False

    def get_user_permissions(self, user_id: str) -> set[AccessLevel]:
        """Get all permissions for a user."""
        return self.user_permissions.get(user_id, set()).copy()

    def revoke_user_access(self, user_id: str) -> bool:
        """Revoke all access for a user."""
        with self._lock:
            if user_id in self.user_permissions:
                del self.user_permissions[user_id]

                # Mark all requests as expired
                for request in self.access_requests:
                    if request.user_id == user_id:
                        request.expires_at = datetime.now()

                return True
            return False

    def get_access_requests(self, user_id: str | None = None, status: str | None = None) -> list[AccessRequest]:
        """Get access requests with optional filtering."""
        requests = self.access_requests.copy()

        if user_id:
            requests = [r for r in requests if r.user_id == user_id]

        if status:
            if status == "approved":
                requests = [r for r in requests if r.approved]
            elif status == "pending":
                requests = [r for r in requests if not r.approved and not r.expired()]
            elif status == "denied":
                requests = [r for r in requests if not r.approved and "denied_by" in r.metadata]
            elif status == "expired":
                requests = [r for r in requests if r.expired()]

        return requests

    def cleanup_expired_requests(self) -> int:
        """Clean up expired access requests."""
        with self._lock:
            original_count = len(self.access_requests)
            self.access_requests = [r for r in self.access_requests if not r.expired()]
            return original_count - len(self.access_requests)


class GDPRComplianceManager:
    """Manages GDPR compliance features including consent management and right to be forgotten."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize GDPR compliance manager."""
        self.config = config or CacheConfig()
        self.consents: dict[str, ConsentRecord] = {}
        self.user_data: dict[str, dict[str, Any]] = defaultdict(dict)
        self.data_subject_requests: list[dict[str, Any]] = []
        self._lock = Lock()

    def record_consent(
        self,
        user_id: str,
        data_types: list[str],
        purpose: str,
        retention_days: int = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> str:
        """Record user consent for data processing."""
        consent_id = secrets.token_urlsafe(32)

        consent = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            data_types=data_types,
            purpose=purpose,
            consent_given=True,
            ip_address=ip_address,
            user_agent=user_agent,
            retention_days=retention_days or self.config.consent_retention_days,
        )

        with self._lock:
            self.consents[consent_id] = consent

        return consent_id

    def withdraw_consent(self, consent_id: str, reason: str = "") -> bool:
        """Withdraw user consent."""
        with self._lock:
            if consent_id in self.consents:
                consent = self.consents[consent_id]
                consent.consent_given = False
                consent.withdrawal_timestamp = datetime.now()
                consent.withdrawal_reason = reason
                return True
            return False

    def check_consent(self, user_id: str, data_type: str, purpose: str) -> bool:
        """Check if user has given consent for specific data processing."""
        with self._lock:
            for consent in self.consents.values():
                if (
                    consent.user_id == user_id
                    and consent.consent_given
                    and data_type in consent.data_types
                    and consent.purpose == purpose
                    and not consent.expired()
                ):
                    return True
        return False

    def get_user_consents(self, user_id: str) -> list[ConsentRecord]:
        """Get all consents for a user."""
        with self._lock:
            return [consent for consent in self.consents.values() if consent.user_id == user_id]

    def add_user_data(self, user_id: str, data_type: str, data: Any, timestamp: datetime | None = None) -> None:
        """Add user data for GDPR compliance tracking."""
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            self.user_data[user_id][data_type] = {
                "data": data,
                "timestamp": timestamp,
                "last_updated": timestamp,
            }

    def get_user_data(self, user_id: str, data_type: str | None = None) -> dict[str, Any]:
        """Get user data for GDPR compliance."""
        with self._lock:
            if user_id not in self.user_data:
                return {}

            if data_type:
                return self.user_data[user_id].get(data_type, {})
            return self.user_data[user_id].copy()

    def delete_user_data(self, user_id: str, data_type: str | None = None) -> bool:
        """Delete user data for right to be forgotten."""
        with self._lock:
            if user_id not in self.user_data:
                return False

            if data_type:
                if data_type in self.user_data[user_id]:
                    del self.user_data[user_id][data_type]
                    return True
            else:
                del self.user_data[user_id]
                return True

        return False

    def get_right_to_be_forgotten_data(self, user_id: str) -> dict[str, Any]:
        """Get all data for right to be forgotten request."""
        data = {"consents": [], "user_data": {}, "audit_entries": []}

        # Get consents
        with self._lock:
            data["consents"] = [
                {
                    "consent_id": consent.consent_id,
                    "data_types": consent.data_types,
                    "purpose": consent.purpose,
                    "timestamp": consent.timestamp,
                    "withdrawal_timestamp": consent.withdrawal_timestamp,
                    "withdrawal_reason": consent.withdrawal_reason,
                }
                for consent in self.consents.values()
                if consent.user_id == user_id
            ]

            # Get user data
            data["user_data"] = self.user_data.get(user_id, {}).copy()

        return data

    def execute_right_to_be_forgotten(self, user_id: str) -> int:
        """Execute right to be forgotten - delete all user data."""
        deleted_count = 0

        # Delete consents
        with self._lock:
            consent_ids_to_delete = [
                consent_id for consent_id, consent in self.consents.items() if consent.user_id == user_id
            ]

            for consent_id in consent_ids_to_delete:
                del self.consents[consent_id]
                deleted_count += 1

            # Delete user data
            if user_id in self.user_data:
                data_count = len(self.user_data[user_id])
                del self.user_data[user_id]
                deleted_count += data_count

        return deleted_count

    def create_data_subject_request(self, user_id: str, request_type: str, details: dict[str, Any]) -> str:
        """Create a data subject request."""
        request_id = secrets.token_urlsafe(32)

        request = {
            "request_id": request_id,
            "user_id": user_id,
            "request_type": request_type,  # access, rectification, erasure, portability, objection
            "details": details,
            "status": "pending",
            "created_at": datetime.now(),
            "due_date": datetime.now() + timedelta(hours=self.config.data_subject_request_timeout_hours),
            "metadata": {},
        }

        with self._lock:
            self.data_subject_requests.append(request)

        return request_id

    def get_data_subject_requests(self, user_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        """Get data subject requests with optional filtering."""
        requests = self.data_subject_requests.copy()

        if user_id:
            requests = [r for r in requests if r["user_id"] == user_id]

        if status:
            requests = [r for r in requests if r["status"] == status]

        return requests

    def cleanup_expired_consents(self) -> int:
        """Clean up expired consent records."""
        with self._lock:
            original_count = len(self.consents)
            self.consents = {
                consent_id: consent for consent_id, consent in self.consents.items() if not consent.expired()
            }
            return original_count - len(self.consents)


class RetentionPolicyManager:
    """Manages data retention policies and lifecycle management."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize retention policy manager."""
        self.config = config or CacheConfig()
        self.retention_rules: dict[str, dict[str, Any]] = {}
        self.user_data: dict[str, dict[str, Any]] = defaultdict(dict)
        self._lock = Lock()

        # Initialize default retention rules
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default retention rules."""
        for classification, days in self.config.default_retention_days.items():
            rule_id = f"default_{classification.value}"
            rule = {
                "rule_id": rule_id,
                "name": f"Default {classification.value} retention",
                "data_classification": classification,
                "retention_days": days,
                "action": "delete",
                "enabled": True,
                "created_at": datetime.now(),
            }
            self.retention_rules[rule_id] = rule

    def create_rule(
        self,
        rule_id: str,
        name: str,
        data_classification: DataClassification,
        retention_days: int,
        action: str = "delete",
        enabled: bool = True,
    ) -> bool:
        """Create a new retention rule."""
        rule = {
            "name": name,
            "data_classification": data_classification,
            "retention_days": retention_days,
            "action": action,
            "enabled": enabled,
            "created_at": datetime.now(),
        }

        with self._lock:
            if rule_id in self.retention_rules:
                return False

            self.retention_rules[rule_id] = rule
            return True

    def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        """Get a retention rule by ID."""
        return self.retention_rules.get(rule_id)

    def get_rules(self, classification: DataClassification | None = None) -> list[dict[str, Any]]:
        """Get all retention rules as a list, optionally filtered by classification."""
        rules = list(self.retention_rules.values())
        if classification is not None:
            rules = [rule for rule in rules if rule.get("data_classification") == classification]
        return rules

    def list_rules(self) -> dict[str, dict[str, Any]]:
        """List all retention rules."""
        return self.retention_rules.copy()

    def add_rule(self, rule: dict[str, Any] | Any) -> str:
        """Add a retention rule (accepts both dict and RetentionRule objects)."""
        if hasattr(rule, "rule_id") and hasattr(rule, "data_classification"):
            # Handle RetentionRule object
            rule_dict = {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "data_classification": rule.data_classification,
                "trigger": (rule.trigger.value if hasattr(rule.trigger, "value") else rule.trigger),
                "action": (rule.action.value if hasattr(rule.action, "value") else rule.action),
                "retention_days": rule.retention_days,
                "enabled": getattr(rule, "enabled", True),
                "priority": getattr(rule, "priority", 100),
                "created_at": getattr(rule, "created", datetime.now()),
                "last_modified": getattr(rule, "last_modified", datetime.now()),
                "conditions": getattr(rule, "conditions", {}),
            }
            rule_id = rule_dict["rule_id"]
        else:
            # Handle dict
            rule_dict = rule
            rule_id = rule_dict.get("rule_id", str(uuid.uuid4()))

        with self._lock:
            if rule_id in self.retention_rules:
                raise ValueError(f"Rule with ID {rule_id} already exists")
            self.retention_rules[rule_id] = rule_dict
        return rule_id

    def delete_rule(self, rule_id: str) -> str:
        """Delete a retention rule and return the deleted rule."""
        with self._lock:
            if rule_id in self.retention_rules:
                deleted_rule = self.retention_rules[rule_id]
                del self.retention_rules[rule_id]
                return True
            return False

    def should_retain(self, metadata: CacheEntryMetadata) -> bool:
        """Check if data should be retained based on policies."""
        classification = metadata.data_classification

        # Find applicable rule
        rule = None
        for rule_data in self.retention_rules.values():
            if rule_data["data_classification"] == classification and rule_data["enabled"]:
                rule = rule_data
                break

        if not rule:
            return True  # Default to retain if no rule found

        # Check retention period
        retention_days = rule["retention_days"]
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        return metadata.created_at > cutoff_date

    def get_expired_entries(self, entries: list[CacheEntryMetadata]) -> list[CacheEntryMetadata]:
        """Get entries that have expired according to retention policies."""
        expired = []

        for metadata in entries:
            if not self.should_retain(metadata):
                expired.append(metadata)

        return expired

    def add_user_data(self, user_id: str, data_type: str, data: Any, timestamp: datetime | None = None) -> None:
        """Add user data with timestamp for retention tracking."""
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            self.user_data[user_id][data_type] = {"data": data, "timestamp": timestamp}

    def cleanup_expired_data(self) -> int:
        """Clean up expired data based on retention policies."""
        deleted_count = 0
        current_time = datetime.now()

        with self._lock:
            for user_id in list(self.user_data.keys()):
                user_data = self.user_data[user_id]

                for data_type in list(user_data.keys()):
                    data_info = user_data[data_type]
                    timestamp = data_info["timestamp"]

                    # Find applicable retention rule
                    rule = None
                    for rule_data in self.retention_rules.values():
                        if rule_data["enabled"]:
                            rule = rule_data
                            break

                    if rule:
                        retention_days = rule["retention_days"]
                        cutoff_date = current_time - timedelta(days=retention_days)

                        if timestamp <= cutoff_date:
                            del user_data[data_type]
                            deleted_count += 1

                # Remove user if no data left
                if not self.user_data[user_id]:
                    del self.user_data[user_id]

        return deleted_count


class CacheSecurityManager:
    """Integrated security manager for cache operations."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize cache security manager."""
        self.config = config or CacheConfig()

        # Initialize components
        self.encryption = CacheEncryption(self.config)
        self.access_control = AccessControlManager(self.config)
        self.gdpr_manager = GDPRComplianceManager(self.config)
        self.retention_manager = RetentionPolicyManager(self.config)

        # Audit trail (simplified for this implementation)
        self.audit_trail: list[AuditEntry] = []
        self._lock = Lock()

    def secure_set(
        self,
        cache,
        key: str,
        value: Any,
        user_id: str,
        data_classification: DataClassification,
        ttl: int | None = None,
        tags: set[str] | None = None,
    ) -> bool:
        """Securely set a value in the cache with encryption and access control."""
        try:
            # Check access permissions
            if not self.config.security.access_control_enabled:
                has_access = True
            else:
                has_access = self.access_control.check_access(user_id, AccessLevel.WRITE, key, data_classification)

            if not has_access:
                self._log_audit_event(
                    "cache_access_denied",
                    user_id,
                    key,
                    "set",
                    "denied",
                    data_classification,
                    "Access denied for write operation",
                )
                return False

            # Check GDPR consent if applicable
            if self.config.security.gdpr_enabled and self.config.is_gdpr_applicable(data_classification):
                has_consent = self.gdpr_manager.check_consent(user_id, "cache_data", "storage")
                if not has_consent:
                    self._log_audit_event(
                        "gdpr_consent_denied",
                        user_id,
                        key,
                        "set",
                        "denied",
                        data_classification,
                        "GDPR consent denied for data storage",
                    )
                    return False

            # Encrypt if required
            processed_value = value
            if self.config.is_encryption_required(data_classification):
                processed_value = self.encryption.encrypt(value)

            # Store in cache
            success = cache.set(key, processed_value, ttl)

            if success:
                # Register for retention management
                if self.config.security.retention_enabled:
                    self.retention_manager.add_user_data(user_id, key, processed_value)

                # Log successful operation
                self._log_audit_event(
                    "cache_access",
                    user_id,
                    key,
                    "set",
                    "success",
                    data_classification,
                    "Cache set operation successful",
                )

            return success

        except Exception as e:
            self._log_audit_event(
                "cache_error",
                user_id,
                key,
                "set",
                "error",
                data_classification,
                f"Cache set error: {e!s}",
            )
            return False

    def secure_get(self, cache, key: str, user_id: str, data_classification: DataClassification) -> Any:
        """Securely get a value from the cache with access control."""
        try:
            # Check access permissions
            if not self.config.security.access_control_enabled:
                has_access = True
            else:
                has_access = self.access_control.check_access(user_id, AccessLevel.READ, key, data_classification)

            if not has_access:
                self._log_audit_event(
                    "cache_access_denied",
                    user_id,
                    key,
                    "get",
                    "denied",
                    data_classification,
                    "Access denied for read operation",
                )
                return None

            # Get from cache
            cached_value = cache.get(key)

            if cached_value is None:
                self._log_audit_event(
                    "cache_miss",
                    user_id,
                    key,
                    "get",
                    "success",
                    data_classification,
                    "Cache miss",
                )
                return None

            # Decrypt if encrypted
            processed_value = cached_value
            if self.config.is_encryption_required(data_classification):
                if isinstance(cached_value, bytes):
                    processed_value = self.encryption.decrypt(cached_value)
                else:
                    processed_value = cached_value

            # Log successful operation
            self._log_audit_event(
                "cache_access",
                user_id,
                key,
                "get",
                "success",
                data_classification,
                "Cache get operation successful",
            )

            return processed_value

        except Exception as e:
            self._log_audit_event(
                "cache_error",
                user_id,
                key,
                "get",
                "error",
                data_classification,
                f"Cache get error: {e!s}",
            )
            return None

    def secure_delete(self, cache, key: str, user_id: str, data_classification: DataClassification) -> bool:
        """Securely delete a value from the cache with access control."""
        try:
            # Check access permissions
            if not self.config.security.access_control_enabled:
                has_access = True
            else:
                has_access = self.access_control.check_access(user_id, AccessLevel.DELETE, key, data_classification)

            if not has_access:
                self._log_audit_event(
                    "cache_access_denied",
                    user_id,
                    key,
                    "delete",
                    "denied",
                    data_classification,
                    "Access denied for delete operation",
                )
                return False

            # Delete from cache
            success = cache.delete(key)

            if success:
                # Clean up retention data
                if self.config.security.retention_enabled:
                    self.retention_manager.delete_user_data(user_id, key)

                # Log successful operation
                self._log_audit_event(
                    "cache_access",
                    user_id,
                    key,
                    "delete",
                    "success",
                    data_classification,
                    "Cache delete operation successful",
                )

            return success

        except Exception as e:
            self._log_audit_event(
                "cache_error",
                user_id,
                key,
                "delete",
                "error",
                data_classification,
                f"Cache delete error: {e!s}",
            )
            return False

    def get_security_metrics(self) -> SecurityMetrics:
        """Get comprehensive security metrics."""
        with self._lock:
            return SecurityMetrics(
                encryption_enabled=self.config.security.encryption_enabled,
                access_control_enabled=self.config.security.access_control_enabled,
                gdpr_enabled=self.config.security.gdpr_enabled,
                retention_enabled=self.config.security.retention_enabled,
                audit_enabled=self.config.security.audit_enabled,
                audit_entries_count=len(self.audit_trail),
                active_policies=len(self.access_control.policies),
                pending_requests=len(self.access_control.get_access_requests(status="pending")),
                approved_requests=len(self.access_control.get_access_requests(status="approved")),
                denied_requests=len(self.access_control.get_access_requests(status="denied")),
            )

    def _log_audit_event(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        outcome: str,
        data_classification: DataClassification,
        details: str = "",
    ) -> None:
        """Log an audit event."""
        if not self.config.security.audit_enabled:
            return

        entry = AuditEntry(
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            outcome=outcome,
            data_classification=data_classification,
            metadata={"details": details} if details else {},
        )

        with self._lock:
            self.audit_trail.append(entry)

            # Trim audit trail if it gets too large
            max_entries = self.config.max_audit_entries_per_query
            if len(self.audit_trail) > max_entries:
                self.audit_trail = self.audit_trail[-max_entries:]

    def get_audit_trail(
        self,
        user_id: str | None = None,
        event_type: str | None = None,
        limit: int | None = None,
    ) -> list[AuditEntry]:
        """Get audit trail with optional filtering."""
        trail = self.audit_trail.copy()

        if user_id:
            trail = [entry for entry in trail if entry.user_id == user_id]

        if event_type:
            trail = [entry for entry in trail if entry.event_type == event_type]

        if limit:
            trail = trail[-limit:]

        return trail


# Export main classes
__all__ = [
    "AccessControlManager",
    "CacheEncryption",
    "CacheSecurityManager",
    "GDPRComplianceManager",
    "RetentionPolicyManager",
]
