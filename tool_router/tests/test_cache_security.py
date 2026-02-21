"""
Cache Security Module Tests

Comprehensive tests for the cache security module including:
- Encryption and decryption functionality
- Access control management
- GDPR compliance features
- Retention policy management
- Audit trail functionality
- Integration testing

Test Coverage Goals:
- Unit tests for individual components
- Integration tests for component interactions
- Error handling and edge cases
- Performance testing
- Security validation
"""

import pytest
import time
import json
import secrets
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from threading import Lock
from cryptography.fernet import Fernet, InvalidToken

# Import the cache security modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cache.config import CacheConfig, load_config_from_env
from cache.types import (
    DataClassification, AccessLevel, ComplianceStandard, SecurityPolicy,
    AccessRequest, AuditEntry, ConsentRecord, CacheEntryMetadata, SecurityMetrics,
    CacheOperationResult, CacheSecurityError, EncryptionError,
    AccessControlError, ComplianceError, RetentionError, AuditError
)
from cache.security import (
    CacheEncryption, AccessControlManager, GDPRComplianceManager,
    RetentionPolicyManager, CacheSecurityManager
)
from cache.compliance import ComplianceManager, GDPRComplianceHandler
from cache.retention import RetentionPolicyManager as RetentionPolicyManagerMain, LifecycleManager


class TestCacheConfig:
    """Test cache configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()
        
        assert config.encryption_enabled is True
        assert config.audit_enabled is True
        assert config.access_control_enabled is True
        assert config.gdpr_compliance_enabled is True
        assert config.retention_enabled is True
        assert config.encryption_key is None
        assert config.audit_max_entries == 10000
        assert config.audit_retention_days == 90
    
    def test_retention_days_configuration(self):
        """Test retention days configuration."""
        config = CacheConfig()
        
        # Check default retention periods
        assert DataClassification.SENSITIVE in config.retention_days
        assert DataClassification.CONFIDENTIAL in config.retention_days
        assert DataClassification.PUBLIC in config.retention_days
        assert DataClassification.INTERNAL in config.retention_days
        
        # Check reasonable default values
        assert config.retention_days[DataClassification.SENSITIVE] >= 30
        assert config.retention_days[DataClassification.CONFIDENTIAL] >= 7
        assert config.retention_days[DataClassification.PUBLIC] >= 180
        assert config.retention_days[DataClassification.INTERNAL] >= 90
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = CacheConfig()
        
        # Valid configuration should pass
        config.validate()  # Should not raise
        
        # Test with invalid retention days
        config.retention_days[DataClassification.SENSITIVE] = -1
        with pytest.raises(ValueError):
            config.validate()
    
    def test_environment_loading(self):
        """Test loading configuration from environment."""
        # Mock environment variables
        env_vars = {
            'CACHE_ENCRYPTION_ENABLED': 'true',
            'CACHE_AUDIT_ENABLED': 'false',
            'CACHE_RETENTION_DAYS_SENSITIVE': '60',
            'CACHE_RETENTION_DAYS_CONFIDENTIAL': '30'
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config_from_env()
            
            assert config.encryption_enabled is True
            assert config.audit_enabled is False
            assert config.retention_days[DataClassification.SENSITIVE] == 60
            assert config.retention_days[DataClassification.CONFIDENTIAL] == 30


class TestCacheEncryption:
    """Test cache encryption functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.encryption = CacheEncryption(self.config)
    
    def test_encryption_key_generation(self):
        """Test encryption key generation."""
        key = self.encryption.generate_key()
        
        assert key is not None
        assert len(key) > 0
        # Fernet keys are 44 bytes base64 encoded
        assert len(key) == 44
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption and decryption roundtrip."""
        test_data = "This is sensitive test data"
        classification = DataClassification.SENSITIVE
        
        # Encrypt
        result = self.encryption.encrypt(test_data, classification)
        
        assert result.encrypted_data is not None
        assert result.operation_id is not None
        assert result.encrypted_data != test_data
        assert result.timestamp is not None
        
        # Decrypt
        decrypt_result = self.encryption.decrypt(
            result.encrypted_data, 
            result.operation_id
        )
        
        assert decrypt_result.decrypted_data == test_data
        assert decrypt_result.timestamp is not None
    
    def test_encryption_with_different_classifications(self):
        """Test encryption with different data classifications."""
        test_data = "Test data for classification"
        
        classifications = [
            DataClassification.PUBLIC,
            DataClassification.INTERNAL,
            DataClassification.SENSITIVE,
            DataClassification.CONFIDENTIAL
        ]
        
        for classification in classifications:
            result = self.encryption.encrypt(test_data, classification)
            decrypt_result = self.encryption.decrypt(
                result.encrypted_data,
                result.operation_id
            )
            
            assert decrypt_result.decrypted_data == test_data
    
    def test_encryption_key_rotation(self):
        """Test encryption key rotation."""
        test_data = "Test data for key rotation"
        
        # Encrypt with original key
        result1 = self.encryption.encrypt(test_data, DataClassification.SENSITIVE)
        
        # Rotate key
        old_key = self.encryption._encryption_key
        self.encryption.rotate_key()
        new_key = self.encryption._encryption_key
        
        assert old_key != new_key
        
        # New encryption should work with new key
        result2 = self.encryption.encrypt(test_data, DataClassification.SENSITIVE)
        decrypt_result2 = self.encryption.decrypt(
            result2.encrypted_data,
            result2.operation_id
        )
        assert decrypt_result2.decrypted_data == test_data
        
        # Old encrypted data should still be decryptable
        decrypt_result1 = self.encryption.decrypt(
            result1.encrypted_data,
            result1.operation_id
        )
        assert decrypt_result1.decrypted_data == test_data
    
    def test_encryption_with_custom_key(self):
        """Test encryption with custom key."""
        custom_key = Fernet.generate_key().decode()
        config = CacheConfig(encryption_key=custom_key)
        encryption = CacheEncryption(config)
        
        test_data = "Test data with custom key"
        result = encryption.encrypt(test_data, DataClassification.SENSITIVE)
        
        decrypt_result = encryption.decrypt(
            result.encrypted_data,
            result.operation_id
        )
        
        assert decrypt_result.decrypted_data == test_data
    
    def test_encryption_disabled(self):
        """Test behavior when encryption is disabled."""
        config = CacheConfig(encryption_enabled=False)
        encryption = CacheEncryption(config)
        
        test_data = "Test data with encryption disabled"
        
        # Should return data as-is when encryption is disabled
        result = encryption.encrypt(test_data, DataClassification.SENSITIVE)
        assert result.encrypted_data == test_data
        
        decrypt_result = encryption.decrypt(test_data, "dummy_id")
        assert decrypt_result.decrypted_data == test_data
    
    def test_encryption_errors(self):
        """Test encryption error handling."""
        # Test invalid encrypted data
        with pytest.raises(EncryptionError):
            self.encryption.decrypt("invalid_encrypted_data", "dummy_id")
        
        # Test with invalid operation ID
        with pytest.raises(EncryptionError):
            self.encryption.decrypt("invalid_data", "nonexistent_id")


class TestAccessControlManager:
    """Test access control management."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.access_manager = AccessControlManager(self.config)
    
    def test_role_based_access_control(self):
        """Test role-based access control."""
        # Test admin access
        result = self.access_manager.check_access(
            "admin_user", "resource_123", AccessLevel.READ
        )
        assert result.access_granted is True
        assert "Admin access" in result.reason
        
        # Test regular user access
        result = self.access_manager.check_access(
            "regular_user", "resource_123", AccessLevel.READ
        )
        assert result.access_granted is True
        assert "User access" in result.reason
        
        # Test restricted access
        result = self.access_manager.check_access(
            "restricted_user", "resource_123", AccessLevel.ADMIN
        )
        assert result.access_granted is False
        assert "Insufficient privileges" in result.reason
    
    def test_access_request_workflow(self):
        """Test access request workflow."""
        # Create access request
        request = AccessRequest(
            request_id="req_123",
            user_id="user_456",
            resource_id="resource_789",
            requested_level=AccessLevel.WRITE,
            justification="Need to update configuration",
            status="pending",
            created=datetime.utcnow()
        )
        
        # Submit request
        request_id = self.access_manager.submit_access_request(request)
        assert request_id == "req_123"
        
        # Check request status
        retrieved_request = self.access_manager.get_access_request(request_id)
        assert retrieved_request is not None
        assert retrieved_request.user_id == "user_456"
        assert retrieved_request.status == "pending"
        
        # Approve request
        success = self.access_manager.approve_access_request(request_id, "admin_user")
        assert success is True
        
        # Check updated status
        updated_request = self.access_manager.get_access_request(request_id)
        assert updated_request.status == "approved"
        assert updated_request.approved_by == "admin_user"
        assert updated_request.approved_at is not None
    
    def test_permission_inheritance(self):
        """Test permission inheritance."""
        # Create a role with specific permissions
        self.access_manager.create_role(
            "data_analyst",
            [AccessLevel.READ],
            ["analytics_*", "reports_*"]
        )
        
        # Assign role to user
        self.access_manager.assign_role("user_123", "data_analyst")
        
        # Test access to allowed resource
        result = self.access_manager.check_access(
            "user_123", "analytics_dashboard", AccessLevel.READ
        )
        assert result.access_granted is True
        
        # Test access to denied resource
        result = self.access_manager.check_access(
            "user_123", "admin_settings", AccessLevel.READ
        )
        assert result.access_granted is False
    
    def test_access_control_disabled(self):
        """Test behavior when access control is disabled."""
        config = CacheConfig(access_control_enabled=False)
        access_manager = AccessControlManager(config)
        
        # All access should be granted when disabled
        result = access_manager.check_access(
            "any_user", "any_resource", AccessLevel.ADMIN
        )
        assert result.access_granted is True
        assert "Access control disabled" in result.reason
    
    def test_access_control_metrics(self):
        """Test access control metrics."""
        # Perform some access checks
        self.access_manager.check_access("user1", "resource1", AccessLevel.READ)
        self.access_manager.check_access("user2", "resource2", AccessLevel.WRITE)
        self.access_manager.check_access("user3", "resource3", AccessLevel.ADMIN)
        
        metrics = self.access_manager.get_metrics()
        
        assert metrics.total_access_control_checks >= 3
        assert isinstance(metrics.access_denied, int)


class TestGDPRComplianceManager:
    """Test GDPR compliance management."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.gdpr_manager = GDPRComplianceManager(self.config)
    
    def test_consent_recording(self):
        """Test consent recording and retrieval."""
        consent_data = {
            'data_types': ['personal_data', 'analytics_data'],
            'purposes': ['marketing', 'analytics'],
            'legal_basis': 'consent'
        }
        
        consent_id = self.gdpr_manager.record_consent("subject_123", consent_data)
        
        assert consent_id is not None
        assert len(consent_id) == 32  # Hex string length
        
        # Check consent exists
        assert self.gdpr_manager.check_consent(
            "subject_123", "personal_data", "marketing"
        ) is True
    
    def test_consent_withdrawal(self):
        """Test consent withdrawal."""
        consent_data = {
            'data_types': ['personal_data'],
            'purposes': ['marketing'],
            'legal_basis': 'consent'
        }
        
        consent_id = self.gdpr_manager.record_consent("subject_456", consent_data)
        
        # Initially should have consent
        assert self.gdpr_manager.check_consent(
            "subject_456", "personal_data", "marketing"
        ) is True
        
        # Withdraw consent
        success = self.gdpr_manager.withdraw_consent(consent_id)
        assert success is True
        
        # Should no longer have consent
        assert self.gdpr_manager.check_consent(
            "subject_456", "personal_data", "marketing"
        ) is False
    
    def test_consent_expiration(self):
        """Test consent expiration."""
        consent_data = {
            'data_types': ['personal_data'],
            'purposes': ['analytics'],
            'legal_basis': 'consent'
        }
        
        consent_id = self.gdpr_manager.record_consent("subject_789", consent_data)
        
        # Manually set expiration to past
        with self.gdpr_manager._lock:
            if consent_id in self.gdpr_manager._consent_records:
                self.gdpr_manager._consent_records[consent_id].expires_at = \
                    datetime.utcnow() - timedelta(days=1)
        
        # Should not have consent due to expiration
        assert self.gdpr_manager.check_consent(
            "subject_789", "personal_data", "analytics"
        ) is False
    
    def test_right_to_be_forgotten(self):
        """Test GDPR right to be forgotten."""
        result = self.gdpr_manager.process_right_to_be_forgotten("subject_999")
        
        assert 'subject_id' in result
        assert result['subject_id'] == "subject_999"
        assert 'processed_at' in result
        assert 'records_deleted' in result
        assert 'cache_entries_cleared' in result
    
    def test_data_subject_requests(self):
        """Test data subject request management."""
        request_data = {
            'request_type': 'access',
            'subject_id': 'subject_111',
            'subject_contact': 'user@example.com',
            'description': 'Request for data access'
        }
        
        request_id = self.gdpr_manager.create_data_subject_request(request_data)
        
        assert request_id is not None
        assert len(request_id) == 32
        
        # Retrieve request
        requests = self.gdpr_manager.get_data_subject_requests("subject_111")
        assert len(requests) == 1
        assert requests[0].subject_id == "subject_111"
        assert requests[0].request_type.value == "access"


class TestRetentionPolicyManager:
    """Test retention policy management."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.retention_manager = RetentionPolicyManager(self.config)
    
    def test_default_retention_rules(self):
        """Test default retention rules are created."""
        rules = self.retention_manager.get_rules()
        
        assert len(rules) >= 4  # Should have rules for all classifications
        
        # Check for required classifications
        classifications = [rule.data_classification for rule in rules]
        assert DataClassification.SENSITIVE in classifications
        assert DataClassification.CONFIDENTIAL in classifications
        assert DataClassification.PUBLIC in classifications
        assert DataClassification.INTERNAL in classifications
    
    def test_add_custom_retention_rule(self):
        """Test adding custom retention rules."""
        from cache.retention import RetentionRule, RetentionAction, RetentionTrigger
        
        custom_rule = RetentionRule(
            rule_id="custom_rule_1",
            name="Custom Test Rule",
            description="Test rule for custom data",
            data_classification=DataClassification.SENSITIVE,
            trigger=RetentionTrigger.TIME_BASED,
            action=RetentionAction.DELETE,
            retention_days=45,
            priority=150
        )
        
        rule_id = self.retention_manager.add_rule(custom_rule)
        assert rule_id == "custom_rule_1"
        
        # Retrieve rule
        rules = self.retention_manager.get_rules(DataClassification.SENSITIVE)
        custom_rules = [r for r in rules if r.rule_id == "custom_rule_1"]
        assert len(custom_rules) == 1
        assert custom_rules[0].retention_days == 45
    
    def test_retention_evaluation(self):
        """Test retention rule evaluation."""
        # Create test metadata
        metadata = CacheEntryMetadata(
            key="test_key",
            data_classification=DataClassification.SENSITIVE,
            created=datetime.utcnow() - timedelta(days=100),  # 100 days old
            last_accessed=datetime.utcnow() - timedelta(days=50),
            size_bytes=1024,
            access_count=10,
            encrypted=True
        )
        
        # Evaluate retention
        applicable_rule = self.retention_manager.evaluate_retention(metadata)
        
        assert applicable_rule is not None
        assert applicable_rule.data_classification == DataClassification.SENSITIVE
        assert applicable_rule.trigger.value == "time_based"
        assert applicable_rule.action.value == "delete"
    
    def test_retention_action_application(self):
        """Test applying retention actions."""
        from cache.retention import RetentionAction
        
        # Create test metadata
        metadata = CacheEntryMetadata(
            key="test_key_2",
            data_classification=DataClassification.PUBLIC,
            created=datetime.utcnow() - timedelta(days=400),  # Very old
            size_bytes=2048,
            access_count=5
        )
        
        # Mock cache delete function
        mock_delete = Mock(return_value=True)
        
        # Apply retention
        result = self.retention_manager.apply_retention_action(
            "test_key_2", metadata, mock_delete
        )
        
        assert result.action == RetentionAction.DELETE
        assert result.items_processed == 1
        assert result.items_deleted == 1
        assert len(result.errors) == 0
        assert result.duration_seconds >= 0
        
        # Verify delete was called
        mock_delete.assert_called_once_with("test_key_2")
    
    def test_retention_rule_update(self):
        """Test updating retention rules."""
        # Get initial rule
        rules = self.retention_manager.get_rules(DataClassification.SENSITIVE)
        initial_rule = rules[0]
        initial_days = initial_rule.retention_days
        
        # Update rule
        updates = {'retention_days': 120, 'enabled': False}
        success = self.retention_manager.update_rule(initial_rule.rule_id, updates)
        
        assert success is True
        
        # Verify update
        updated_rules = self.retention_manager.get_rules(DataClassification.SENSITIVE)
        updated_rule = next(r for r in updated_rules if r.rule_id == initial_rule.rule_id)
        
        assert updated_rule.retention_days == 120
        assert updated_rule.enabled is False
        assert updated_rule.retention_days != initial_days
    
    def test_retention_rule_deletion(self):
        """Test deleting retention rules."""
        # Add a test rule
        from cache.retention import RetentionRule, RetentionAction, RetentionTrigger
        
        test_rule = RetentionRule(
            rule_id="test_delete_rule",
            name="Test Delete Rule",
            description="Rule for testing deletion",
            data_classification=DataClassification.INTERNAL,
            trigger=RetentionTrigger.TIME_BASED,
            action=RetentionAction.DELETE,
            retention_days=30
        )
        
        self.retention_manager.add_rule(test_rule)
        
        # Verify rule exists
        rules_before = self.retention_manager.get_rules()
        rule_ids_before = [r.rule_id for r in rules_before]
        assert "test_delete_rule" in rule_ids_before
        
        # Delete rule
        success = self.retention_manager.delete_rule("test_delete_rule")
        assert success is True
        
        # Verify rule is deleted
        rules_after = self.retention_manager.get_rules()
        rule_ids_after = [r.rule_id for r in rules_after]
        assert "test_delete_rule" not in rule_ids_after


class TestCacheSecurityManager:
    """Test integrated cache security manager."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.security_manager = CacheSecurityManager(self.config)
    
    def test_integrated_encryption_workflow(self):
        """Test integrated encryption workflow."""
        test_data = "Sensitive integrated test data"
        
        # Encrypt through security manager
        result = self.security_manager.encrypt_data(
            test_data, DataClassification.SENSITIVE
        )
        
        assert result.encrypted_data is not None
        assert result.operation_id is not None
        
        # Decrypt through security manager
        decrypt_result = self.security_manager.decrypt_data(
            result.encrypted_data, result.operation_id
        )
        
        assert decrypt_result.decrypted_data == test_data
    
    def test_integrated_access_control_workflow(self):
        """Test integrated access control workflow."""
        # Check access through security manager
        result = self.security_manager.check_access(
            "admin_user", "secure_resource", AccessLevel.ADMIN
        )
        
        assert result.access_granted is True
        assert result.reason is not None
        assert result.timestamp is not None
    
    def test_integrated_audit_logging(self):
        """Test integrated audit logging."""
        # Perform some operations that should be audited
        self.security_manager.encrypt_data("audit_test", DataClassification.PUBLIC)
        self.security_manager.check_access("test_user", "test_resource", AccessLevel.READ)
        
        # Check audit trail
        audit_entries = self.security_manager.get_audit_entries(limit=10)
        
        assert len(audit_entries) >= 2
        
        # Check specific events
        encryption_events = [e for e in audit_entries if e.event_type == "data_encryption"]
        access_events = [e for e in audit_entries if e.event_type == "access_check"]
        
        assert len(encryption_events) >= 1
        assert len(access_events) >= 1
    
    def test_integrated_metrics_collection(self):
        """Test integrated metrics collection."""
        # Perform various operations
        self.security_manager.encrypt_data("metrics_test", DataClassification.INTERNAL)
        self.security_manager.check_access("metrics_user", "metrics_resource", AccessLevel.WRITE)
        
        # Get metrics
        metrics = self.security_manager.get_metrics()
        
        assert metrics.total_encryption_operations >= 1
        assert metrics.total_access_control_checks >= 1
        assert isinstance(metrics.encryption_errors, int)
        assert isinstance(metrics.access_denied, int)
    
    def test_secure_cache_operations(self):
        """Test secure cache operations."""
        # Test secure storage
        key = "secure_key_123"
        data = "Secure cache data"
        classification = DataClassification.CONFIDENTIAL
        
        result = self.security_manager.secure_store(key, data, classification)
        
        assert result.success is True
        assert result.operation_id is not None
        assert result.encrypted is True
        
        # Test secure retrieval
        retrieve_result = self.security_manager.secure_retrieve(key)
        
        assert retrieve_result.success is True
        assert retrieve_result.data == data
        assert retrieve_result.decrypted is True
    
    def test_security_configuration_changes(self):
        """Test dynamic security configuration changes."""
        # Test with encryption enabled
        assert self.security_manager.is_encryption_enabled() is True
        
        # Disable encryption
        self.security_manager.configure_encryption(enabled=False)
        assert self.security_manager.is_encryption_enabled() is False
        
        # Test encryption when disabled
        result = self.security_manager.encrypt_data("test", DataClassification.PUBLIC)
        assert result.encrypted_data == "test"  # Should return as-is when disabled
        
        # Re-enable encryption
        self.security_manager.configure_encryption(enabled=True)
        assert self.security_manager.is_encryption_enabled() is True
    
    def test_error_handling_integration(self):
        """Test error handling across integrated components."""
        # Test with invalid data
        with pytest.raises(CacheSecurityError):
            self.security_manager.decrypt_data("invalid_data", "invalid_id")
        
        # Test with invalid access parameters
        result = self.security_manager.check_access("", "", AccessLevel.ADMIN)
        assert result.access_granted is False
        assert "Invalid" in result.reason


class TestComplianceManager:
    """Test compliance manager integration."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.compliance_manager = ComplianceManager(self.config)
    
    def test_consent_management_integration(self):
        """Test consent management through compliance manager."""
        consent_data = {
            'data_types': ['email', 'name'],
            'purposes': ['communication'],
            'legal_basis': 'consent'
        }
        
        consent_id = self.compliance_manager.record_consent("user_123", consent_data)
        assert consent_id is not None
        
        # Check consent
        has_consent = self.compliance_manager.check_consent(
            "user_123", "email", "communication"
        )
        assert has_consent is True
        
        # Withdraw consent
        success = self.compliance_manager.withdraw_consent(consent_id)
        assert success is True
        
        # Check consent after withdrawal
        has_consent = self.compliance_manager.check_consent(
            "user_123", "email", "communication"
        )
        assert has_consent is False
    
    def test_data_subject_request_integration(self):
        """Test data subject request handling."""
        request_data = {
            'request_type': 'erasure',
            'subject_id': 'user_456',
            'subject_contact': 'user@example.com',
            'description': 'Request data deletion'
        }
        
        request_id = self.compliance_manager.create_data_subject_request(request_data)
        assert request_id is not None
        
        # Get requests
        requests = self.compliance_manager.get_data_subject_requests("user_456")
        assert len(requests) == 1
        assert requests[0].request_type.value == "erasure"
    
    def test_compliance_assessment(self):
        """Test compliance assessment functionality."""
        assessment = self.compliance_manager.assess_compliance(ComplianceStandard.GDPR)
        
        assert assessment.standard == ComplianceStandard.GDPR
        assert assessment.score >= 0
        assert assessment.score <= 100
        assert len(assessment.findings) >= 0
        assert len(assessment.recommendations) >= 0
        assert assessment.last_assessed is not None
        assert assessment.next_assessed is not None
    
    def test_compliance_reporting(self):
        """Test compliance report generation."""
        report = self.compliance_manager.generate_compliance_report()
        
        assert report.report_id is not None
        assert report.period_start is not None
        assert report.period_end is not None
        assert len(report.standards) >= 1
        assert len(report.assessments) >= 1
        assert report.generated is not None
        assert report.generated_by is not None
    
    def test_compliance_metrics(self):
        """Test compliance metrics collection."""
        # Perform some compliance operations
        self.compliance_manager.record_consent("metrics_user", {
            'data_types': ['test'],
            'purposes': ['test'],
            'legal_basis': 'consent'
        })
        
        metrics = self.compliance_manager.get_metrics()
        
        assert metrics.total_compliance_checks >= 1
        assert isinstance(metrics.compliance_violations, int)


class TestIntegrationScenarios:
    """Test integration scenarios between components."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.security_manager = CacheSecurityManager(self.config)
        self.compliance_manager = ComplianceManager(self.config)
        self.retention_manager = RetentionPolicyManager(self.config)
    
    def test_end_to_end_security_workflow(self):
        """Test complete end-to-end security workflow."""
        # Step 1: Record consent for data processing
        consent_id = self.compliance_manager.record_consent("integration_user", {
            'data_types': ['personal_data'],
            'purposes': ['analytics'],
            'legal_basis': 'consent'
        })
        
        # Step 2: Encrypt sensitive data
        sensitive_data = "User's personal information"
        encrypt_result = self.security_manager.encrypt_data(
            sensitive_data, DataClassification.SENSITIVE
        )
        
        # Step 3: Check access permissions
        access_result = self.security_manager.check_access(
            "integration_user", "user_data", AccessLevel.READ
        )
        
        # Step 4: Store data securely (mock)
        metadata = CacheEntryMetadata(
            key="user_profile",
            data_classification=DataClassification.SENSITIVE,
            created=datetime.utcnow(),
            size_bytes=len(sensitive_data),
            encrypted=True
        )
        
        # Step 5: Apply retention policy
        mock_delete = Mock(return_value=True)
        retention_result = self.retention_manager.apply_retention_action(
            "user_profile", metadata, mock_delete
        )
        
        # Verify all steps completed successfully
        assert consent_id is not None
        assert encrypt_result.encrypted_data != sensitive_data
        assert access_result.access_granted is True
        assert retention_result.items_processed == 1
        
        # Step 6: Decrypt and verify data
        decrypt_result = self.security_manager.decrypt_data(
            encrypt_result.encrypted_data, encrypt_result.operation_id
        )
        assert decrypt_result.decrypted_data == sensitive_data
    
    def test_compliance_driven_data_handling(self):
        """Test compliance-driven data handling scenarios."""
        # Scenario 1: Process data without consent
        has_consent = self.compliance_manager.check_consent(
            "no_consent_user", "personal_data", "marketing"
        )
        assert has_consent is False
        
        # Scenario 2: Process data with consent
        consent_id = self.compliance_manager.record_consent("consent_user", {
            'data_types': ['personal_data'],
            'purposes': ['marketing'],
            'legal_basis': 'consent'
        })
        
        has_consent = self.compliance_manager.check_consent(
            "consent_user", "personal_data", "marketing"
        )
        assert has_consent is True
        
        # Scenario 3: Withdraw consent and verify impact
        self.compliance_manager.withdraw_consent(consent_id)
        
        has_consent = self.compliance_manager.check_consent(
            "consent_user", "personal_data", "marketing"
        )
        assert has_consent is False
    
    def test_security_policy_enforcement(self):
        """Test security policy enforcement across components."""
        # Create sensitive data
        test_data = "Highly confidential business data"
        
        # Encrypt with highest classification
        encrypt_result = self.security_manager.encrypt_data(
            test_data, DataClassification.CONFIDENTIAL
        )
        
        # Try to access with insufficient privileges
        access_result = self.security_manager.check_access(
            "low_privilege_user", "confidential_resource", AccessLevel.ADMIN
        )
        assert access_result.access_granted is False
        
        # Access with sufficient privileges
        access_result = self.security_manager.check_access(
            "admin_user", "confidential_resource", AccessLevel.READ
        )
        assert access_result.access_granted is True
        
        # Verify audit trail captures all events
        audit_entries = self.security_manager.get_audit_entries(limit=10)
        
        # Should have encryption and access check events
        event_types = [e.event_type for e in audit_entries]
        assert "data_encryption" in event_types
        assert "access_check" in event_types
    
    def test_retention_policy_compliance(self):
        """Test retention policy compliance."""
        # Create data with different classifications
        sensitive_metadata = CacheEntryMetadata(
            key="sensitive_data",
            data_classification=DataClassification.SENSITIVE,
            created=datetime.utcnow() - timedelta(days=100),  # Old data
            size_bytes=1024,
            encrypted=True
        )
        
        public_metadata = CacheEntryMetadata(
            key="public_data",
            data_classification=DataClassification.PUBLIC,
            created=datetime.utcnow() - timedelta(days=200),  # Very old data
            size_bytes=512,
            encrypted=False
        )
        
        # Evaluate retention for both
        sensitive_rule = self.retention_manager.evaluate_retention(sensitive_metadata)
        public_rule = self.retention_manager.evaluate_retention(public_metadata)
        
        # Both should have applicable rules
        assert sensitive_rule is not None
        assert public_rule is not None
        
        # Sensitive data should have shorter retention
        assert sensitive_rule.retention_days <= public_rule.retention_days
        
        # Mock deletion and apply retention
        mock_delete = Mock(return_value=True)
        
        sensitive_result = self.retention_manager.apply_retention_action(
            "sensitive_data", sensitive_metadata, mock_delete
        )
        
        public_result = self.retention_manager.apply_retention_action(
            "public_data", public_metadata, mock_delete
        )
        
        # Both should be processed
        assert sensitive_result.items_processed == 1
        assert public_result.items_processed == 1
        
        # Verify deletion was called for old data
        assert mock_delete.call_count >= 1


class TestPerformanceAndScalability:
    """Test performance and scalability aspects."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.security_manager = CacheSecurityManager(self.config)
    
    def test_encryption_performance(self):
        """Test encryption performance with various data sizes."""
        data_sizes = [100, 1000, 10000, 100000]  # bytes
        
        for size in data_sizes:
            test_data = "x" * size
            
            start_time = time.time()
            result = self.security_manager.encrypt_data(test_data, DataClassification.PUBLIC)
            encrypt_time = time.time() - start_time
            
            start_time = time.time()
            decrypt_result = self.security_manager.decrypt_data(
                result.encrypted_data, result.operation_id
            )
            decrypt_time = time.time() - start_time
            
            # Performance should be reasonable (adjust thresholds as needed)
            assert encrypt_time < 1.0  # 1 second max
            assert decrypt_time < 1.0  # 1 second max
            assert decrypt_result.decrypted_data == test_data
    
    def test_concurrent_access_control(self):
        """Test concurrent access control checks."""
        import threading
        
        results = []
        errors = []
        
        def check_access(user_id):
            try:
                result = self.security_manager.check_access(
                    user_id, "test_resource", AccessLevel.READ
                )
                results.append(result.access_granted)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=check_access, args=(f"user_{i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations completed
        assert len(errors) == 0
        assert len(results) == 10
        assert all(results)  # All should be granted for basic access
    
    def test_audit_log_scalability(self):
        """Test audit log scalability."""
        # Generate many audit entries
        for i in range(1000):
            self.security_manager.encrypt_data(f"test_data_{i}", DataClassification.PUBLIC)
        
        # Test retrieval performance
        start_time = time.time()
        entries = self.security_manager.get_audit_entries(limit=100)
        retrieval_time = time.time() - start_time
        
        assert len(entries) == 100
        assert retrieval_time < 1.0  # Should be fast
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        import sys
        
        # Get initial memory usage
        initial_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        
        # Create and encrypt many items
        encrypted_items = []
        for i in range(100):
            data = "x" * 1000  # 1KB each
            result = self.security_manager.encrypt_data(data, DataClassification.PUBLIC)
            encrypted_items.append(result)
        
        # Decrypt all items
        for item in encrypted_items:
            self.security_manager.decrypt_data(item.encrypted_data, item.operation_id)
        
        # Memory usage should be reasonable
        final_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        object_increase = final_objects - initial_objects
        
        # Should not create excessive objects (adjust threshold as needed)
        assert object_increase < 10000


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])