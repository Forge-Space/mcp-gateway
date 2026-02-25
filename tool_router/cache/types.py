"""Cache types and configurations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass
class CacheConfig:
    """Configuration for cache instances."""

    max_size: int = 1000
    ttl: int = 3600  # 1 hour default TTL
    cleanup_interval: int = 300  # 5 minutes
    enable_metrics: bool = True

    # Security configuration
    encryption_enabled: bool = True
    audit_enabled: bool = True
    access_control_enabled: bool = True
    gdpr_compliance_enabled: bool = True
    retention_enabled: bool = True
    encryption_key: str | None = None
    audit_max_entries: int = 10000
    audit_retention_days: int = 90

    # Retention periods for different data classifications
    retention_days: dict[DataClassification, int] | None = None

    # Default retention days for different classifications
    default_retention_days: dict[DataClassification, int] | None = None

    def __post_init__(self) -> None:
        """Initialize default retention days if not provided."""
        default_days = {
            DataClassification.PUBLIC: 180,
            DataClassification.INTERNAL: 90,
            DataClassification.SENSITIVE: 30,
            DataClassification.CONFIDENTIAL: 7,
        }

        if self.retention_days is None:
            self.retention_days = default_days.copy()

        if self.default_retention_days is None:
            self.default_retention_days = default_days.copy()

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.max_size < 1:
            raise ValueError("max_size must be positive")
        if self.ttl < 0:
            raise ValueError("ttl must be non-negative")
        if self.cleanup_interval < 0:
            raise ValueError("cleanup_interval must be non-negative")
        if self.audit_max_entries < 1:
            raise ValueError("audit_max_entries must be positive")
        if self.audit_retention_days < 1:
            raise ValueError("audit_retention_days must be positive")

        # Validate retention days
        if self.retention_days:
            for classification, days in self.retention_days.items():
                if days < 1:
                    raise ValueError(f"retention_days for {classification} must be positive")


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    last_reset_time: float = 0.0
    cache_size: int = 0


class DataClassification(Enum):
    """Data classification levels for security handling."""

    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    CONFIDENTIAL = "confidential"


class AccessLevel(Enum):
    """Access levels for permission management."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class CacheEntryMetadata:
    """Metadata for cache entries."""

    key: str
    classification: DataClassification
    created_at: datetime
    expires_at: datetime | None = None
    access_count: int = 0
    last_accessed: datetime | None = None
    owner_id: str | None = None
    tags: list[str] | None = None


@dataclass
class AuditEntry:
    """Audit log entry for security events."""

    event_id: str
    timestamp: datetime
    event_type: str
    user_id: str | None = None
    resource_id: str | None = None
    action: str | None = None
    outcome: str | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class AccessRequest:
    """Access control request."""

    request_id: str
    user_id: str
    resource_id: str
    requested_access: AccessLevel
    timestamp: datetime
    context: dict[str, Any] | None = None
    justification: str | None = None


@dataclass
class ConsentRecord:
    """GDPR consent record."""

    consent_id: str
    subject_id: str = ""
    purpose: str = ""
    legal_basis: str = "consent"
    consent_given: bool = True
    timestamp: datetime | None = None
    expires_at: datetime | None = None
    withdrawn_at: datetime | None = None
    processing_purposes: list[str] | None = None
    data_types: list[str] | None = None
    purposes: list[str] | None = None
    granted: bool = True
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    retention_days: int | None = None
    withdrawal_timestamp: datetime | None = None
    withdrawal_reason: str | None = None

    def expired(self) -> bool:
        """Check if consent has expired."""
        if self.expires_at is None:
            return False
        from datetime import UTC

        return datetime.now(UTC) > self.expires_at


@dataclass
class SecurityMetrics:
    """Security-related metrics."""

    encryption_operations: int = 0
    decryption_operations: int = 0
    access_denied: int = 0
    access_granted: int = 0
    audit_entries: int = 0
    consent_records: int = 0
    data_breaches: int = 0
    security_violations: int = 0
    compliance_violations: int = 0
    total_compliance_checks: int = 0
    encryption_errors: int = 0
    audit_failures: int = 0
    last_updated: datetime | None = None


@dataclass
class SecurityPolicy:
    """Security policy configuration."""

    policy_id: str
    name: str
    description: str
    classification: DataClassification
    retention_days: int
    encryption_required: bool
    access_controls: list[AccessLevel]
    audit_required: bool
    consent_required: bool
    created_at: datetime
    updated_at: datetime | None = None
    active: bool = True


class EncryptionError(Exception):
    """Exception raised during encryption/decryption operations."""


class ComplianceError(Exception):
    """Exception raised during compliance operations."""


class ComplianceStandard(Enum):
    """Compliance standards for security policies."""

    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


@dataclass
class CacheOperationResult:
    """Result of a cache operation."""

    success: bool
    operation: str
    timestamp: datetime
    details: dict[str, Any] | None = None
    error_message: str | None = None


class CacheSecurityError(Exception):
    """Base exception for cache security errors."""


class AccessControlError(CacheSecurityError):
    """Exception raised during access control operations."""


class RetentionError(CacheSecurityError):
    """Exception raised during retention operations."""


class AuditError(CacheSecurityError):
    """Exception raised during audit operations."""
