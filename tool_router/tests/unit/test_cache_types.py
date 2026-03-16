"""Unit tests for tool_router/cache/types.py — shared data structures and exceptions."""

from __future__ import annotations

import datetime
import time

import pytest

from tool_router.cache.types import (
    AccessLevel,
    AccessRequest,
    AuditEntry,
    CacheConfig,
    CacheEntryMetadata,
    CacheMetrics,
    CacheOperationResult,
    CacheSecurityError,
    ComplianceError,
    ComplianceStandard,
    ConsentRecord,
    DataClassification,
    EncryptionError,
    RetentionError,
    SecurityMetrics,
    SecurityPolicy,
)


# ── DataClassification enum ──────────────────────────────────────────────────


def test_data_classification_values() -> None:
    assert DataClassification.PUBLIC.value == "public"
    assert DataClassification.INTERNAL.value == "internal"
    assert DataClassification.SENSITIVE.value == "sensitive"
    assert DataClassification.CONFIDENTIAL.value == "confidential"


def test_data_classification_count() -> None:
    assert len(DataClassification) == 4


def test_data_classification_has_str_values() -> None:
    assert isinstance(DataClassification.PUBLIC.value, str)


# ── AccessLevel enum ─────────────────────────────────────────────────────────


def test_access_level_values() -> None:
    assert AccessLevel.READ.value == "read"
    assert AccessLevel.WRITE.value == "write"
    assert AccessLevel.DELETE.value == "delete"
    assert AccessLevel.ADMIN.value == "admin"


def test_access_level_count() -> None:
    assert len(AccessLevel) == 4


# ── ComplianceStandard enum ───────────────────────────────────────────────────


def test_compliance_standard_values() -> None:
    assert ComplianceStandard.GDPR.value == "gdpr"
    assert ComplianceStandard.CCPA.value == "ccpa"
    assert ComplianceStandard.HIPAA.value == "hipaa"
    assert ComplianceStandard.SOX.value == "sox"
    assert ComplianceStandard.PCI_DSS.value == "pci_dss"
    assert ComplianceStandard.ISO_27001.value == "iso_27001"


def test_compliance_standard_count() -> None:
    assert len(ComplianceStandard) == 6


# ── Exceptions ───────────────────────────────────────────────────────────────


def test_encryption_error_is_exception() -> None:
    err = EncryptionError("bad key")
    assert isinstance(err, Exception)
    assert str(err) == "bad key"


def test_compliance_error_is_exception() -> None:
    err = ComplianceError("violation")
    assert isinstance(err, Exception)


def test_cache_security_error_is_exception() -> None:
    err = CacheSecurityError("security failure")
    assert isinstance(err, Exception)


def test_retention_error_is_exception() -> None:
    err = RetentionError("retention issue")
    assert isinstance(err, Exception)


# ── CacheConfig ───────────────────────────────────────────────────────────────


def test_cache_config_defaults() -> None:
    cfg = CacheConfig()
    assert cfg.max_size == 1000
    assert cfg.ttl == 3600
    assert cfg.cleanup_interval == 300
    assert cfg.enable_metrics is True
    assert cfg.encryption_enabled is True
    assert cfg.audit_enabled is True
    assert cfg.access_control_enabled is True
    assert cfg.gdpr_compliance_enabled is True
    assert cfg.retention_enabled is True
    assert cfg.encryption_key is None


def test_cache_config_post_init_sets_retention_days() -> None:
    cfg = CacheConfig()
    # __post_init__ should set per-classification defaults
    assert cfg.retention_days is not None
    assert DataClassification.PUBLIC in cfg.retention_days
    assert DataClassification.CONFIDENTIAL in cfg.retention_days


def test_cache_config_custom_values() -> None:
    cfg = CacheConfig(max_size=500, ttl=7200)
    assert cfg.max_size == 500
    assert cfg.ttl == 7200


def test_cache_config_validate_valid() -> None:
    cfg = CacheConfig()
    cfg.validate()  # should not raise


def test_cache_config_validate_invalid_max_size() -> None:
    cfg = CacheConfig(max_size=0)
    with pytest.raises(ValueError):
        cfg.validate()


def test_cache_config_validate_invalid_ttl() -> None:
    cfg = CacheConfig(ttl=-1)
    with pytest.raises(ValueError):
        cfg.validate()


# ── CacheMetrics ─────────────────────────────────────────────────────────────


def test_cache_metrics_defaults() -> None:
    m = CacheMetrics()
    assert m.hits == 0
    assert m.misses == 0
    assert m.evictions == 0
    assert m.total_requests == 0
    assert m.hit_rate == 0.0
    assert m.cache_size == 0


def test_cache_metrics_custom() -> None:
    m = CacheMetrics(hits=10, misses=5)
    assert m.hits == 10
    assert m.misses == 5


# ── CacheEntryMetadata ────────────────────────────────────────────────────────


def test_cache_entry_metadata_basic() -> None:
    now = time.time()
    meta = CacheEntryMetadata(
        key="test_key",
        classification=DataClassification.INTERNAL,
        created_at=now,
    )
    assert meta.key == "test_key"
    assert meta.classification == DataClassification.INTERNAL
    assert meta.access_count == 0
    assert meta.owner_id is None
    assert meta.tags is None


def test_cache_entry_metadata_full() -> None:
    now = time.time()
    meta = CacheEntryMetadata(
        key="k",
        classification=DataClassification.SENSITIVE,
        created_at=now,
        expires_at=now + 3600,
        access_count=5,
        last_accessed=now,
        owner_id="user-1",
        tags=["tag1", "tag2"],
    )
    assert meta.owner_id == "user-1"
    assert meta.tags == ["tag1", "tag2"]
    assert meta.access_count == 5


# ── AuditEntry ────────────────────────────────────────────────────────────────


def test_audit_entry_basic() -> None:
    entry = AuditEntry(
        event_id="evt-1",
        timestamp=time.time(),
        event_type="cache_access",
    )
    assert entry.event_id == "evt-1"
    assert entry.event_type == "cache_access"
    assert entry.user_id is None
    assert entry.resource_id is None


def test_audit_entry_full() -> None:
    entry = AuditEntry(
        event_id="evt-2",
        timestamp=time.time(),
        event_type="delete",
        user_id="u1",
        resource_id="r1",
        action="delete",
        outcome="success",
        details={"key": "val"},
        ip_address="127.0.0.1",
        user_agent="test-agent",
    )
    assert entry.user_id == "u1"
    assert entry.outcome == "success"


# ── AccessRequest ─────────────────────────────────────────────────────────────


def test_access_request_basic() -> None:
    req = AccessRequest(
        request_id="req-1",
        user_id="u1",
        resource_id="res-1",
        requested_access=AccessLevel.READ,
        timestamp=time.time(),
    )
    assert req.request_id == "req-1"
    assert req.requested_access == AccessLevel.READ
    assert req.context is None
    assert req.justification is None


# ── ConsentRecord ─────────────────────────────────────────────────────────────


def test_consent_record_defaults() -> None:
    c = ConsentRecord(consent_id="c-1")
    assert c.consent_id == "c-1"
    assert c.consent_given is True
    assert c.granted is True
    assert c.subject_id == ""


def test_consent_record_expired_no_expires_at() -> None:
    c = ConsentRecord(consent_id="c-2")
    assert c.expired() is False


def test_consent_record_expired_future() -> None:
    future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
    c = ConsentRecord(consent_id="c-3", expires_at=future)
    assert c.expired() is False


def test_consent_record_expired_past() -> None:
    past = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=1)
    c = ConsentRecord(consent_id="c-4", expires_at=past)
    assert c.expired() is True


def test_consent_record_withdrawn_at_no_expires() -> None:
    # withdrawn_at alone does not cause expired() to return True (only expires_at does)
    c = ConsentRecord(consent_id="c-5", withdrawn_at=time.time())
    # expires_at is None, so expired() returns False
    assert c.expired() is False


# ── SecurityPolicy ─────────────────────────────────────────────────────────────


def test_security_policy_basic() -> None:
    now = time.time()
    policy = SecurityPolicy(
        policy_id="p-1",
        name="Test Policy",
        description="desc",
        classification=DataClassification.INTERNAL,
        retention_days=90,
        encryption_required=True,
        access_controls=[AccessLevel.READ, AccessLevel.WRITE],
        audit_required=True,
        consent_required=False,
        created_at=now,
        updated_at=now,
        active=True,
    )
    assert policy.policy_id == "p-1"
    assert policy.active is True
    assert AccessLevel.READ in policy.access_controls


# ── SecurityMetrics ───────────────────────────────────────────────────────────


def test_security_metrics_defaults() -> None:
    m = SecurityMetrics(
        encryption_operations=0,
        decryption_operations=0,
        access_denied=0,
        access_granted=0,
        audit_entries=0,
        consent_records=0,
        data_breaches=0,
        security_violations=0,
        compliance_violations=0,
        total_compliance_checks=0,
        encryption_errors=0,
        audit_failures=0,
        last_updated=time.time(),
    )
    assert m.encryption_operations == 0
    assert m.data_breaches == 0


# ── CacheOperationResult ──────────────────────────────────────────────────────


def test_cache_operation_result_success() -> None:
    r = CacheOperationResult(
        success=True,
        operation="set",
        timestamp=time.time(),
        details={"key": "k1"},
        error_message=None,
    )
    assert r.success is True
    assert r.error_message is None


def test_cache_operation_result_failure() -> None:
    r = CacheOperationResult(
        success=False,
        operation="get",
        timestamp=time.time(),
        details={},
        error_message="key not found",
    )
    assert r.success is False
    assert r.error_message == "key not found"
