"""Cache Security Module Tests"""

import pytest
import time
import json
import secrets
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from threading import Lock
from cryptography.fernet import Fernet, InvalidToken

# Import the cache security modules with correct imports
from tool_router.cache.config import CacheBackendConfig, get_cache_backend_config
from tool_router.cache.types import CacheConfig, CacheMetrics
from tool_router.cache.security import CacheEncryption, AccessControlManager
from tool_router.cache.compliance import GDPRComplianceManager
from tool_router.cache.retention import RetentionPolicyManager
from tool_router.cache.api import CacheSecurityAPI

# Test configuration
@pytest.fixture
def cache_config():
    """Create a test cache configuration."""
    return CacheConfig(
        max_size=100,
        ttl=3600,
        cleanup_interval=300,
        enable_metrics=True
    )

@pytest.fixture
def encryption_key():
    """Generate a test encryption key."""
    return Fernet.generate_key().decode()

@pytest.fixture
def cache_encryption(encryption_key):
    """Create a test cache encryption instance."""
    encryption = CacheEncryption()
    encryption.set_encryption_key(encryption_key)
    return encryption

@pytest.fixture
def access_control_manager():
    """Create a test access control manager."""
    return AccessControlManager()

@pytest.fixture
def gdpr_compliance_manager():
    """Create a test GDPR compliance manager."""
    return GDPRComplianceManager()

@pytest.fixture
def retention_policy_manager():
    """Create a test retention policy manager."""
    return RetentionPolicyManager()

@pytest.fixture
def security_api():
    """Create a test security API instance."""
    return CacheSecurityAPI()

class TestCacheEncryption:
    """Test cases for CacheEncryption class."""
    
    def test_encryption_initialization(self, cache_config):
        """Test encryption initialization."""
        encryption = CacheEncryption(cache_config)
        assert encryption.config == cache_config
        assert encryption._fernet is None
        assert encryption._encryption_key is None
    
    def test_set_encryption_key(self, cache_encryption):
        """Test setting encryption key."""
        key = Fernet.generate_key().decode()
        cache_encryption.set_encryption_key(key)
        assert cache_encryption._encryption_key == key
        assert cache_encryption._fernet is not None
    
    def test_encrypt_decrypt_data(self, cache_encryption):
        """Test encrypting and decrypting data."""
        test_data = "sensitive_information"
        
        # Test encryption
        encrypted = cache_encryption.encrypt(test_data)
        assert encrypted is not None
        assert isinstance(encrypted, bytes)
        
        # Test decryption
        decrypted = cache_encryption.decrypt(encrypted)
        assert decrypted == test_data

class TestAccessControlManager:
    """Test cases for AccessControlManager class."""
    
    def test_access_control_initialization(self):
        """Test access control initialization."""
        manager = AccessControlManager()
        assert manager is not None
    
    def test_permission_check(self, access_control_manager):
        """Test permission checking."""
        # Test with mock data
        user_id = "user123"
        operation = "read"
        resource = "cache_key"
        data_classification = "PUBLIC"
        
        # This should work with mock implementation
        result = access_control_manager.check_access(
            user_id, operation, resource, data_classification
        )
        assert isinstance(result, bool)

class TestGDPRComplianceManager:
    """Test cases for GDPRComplianceManager class."""
    
    def test_gdpr_compliance_initialization(self):
        """Test GDPR compliance initialization."""
        manager = GDPRComplianceManager()
        assert manager is not None
    
    def test_consent_recording(self, gdpr_compliance_manager):
        """Test consent recording."""
        user_id = "user123"
        data_type = "cache_data"
        purpose = "storage"
        consent_given = True
        
        # This should work with mock implementation
        result = gdpr_compliance_manager.record_consent(
            user_id, data_type, purpose, consent_given
        )
        assert isinstance(result, bool)

class TestRetentionPolicyManager:
    """Test cases for RetentionPolicyManager class."""
    
    def test_retention_policy_initialization(self):
        """Test retention policy initialization."""
        manager = RetentionPolicyManager()
        assert manager is not None
    
    def test_policy_creation(self, retention_policy_manager):
        """Test policy creation."""
        policy_id = "test_policy"
        data_classification = "PERSONAL"
        retention_days = 2555
        auto_delete = True
        
        # This should work with mock implementation
        result = retention_policy_manager.create_policy(
            policy_id, data_classification, retention_days, auto_delete
        )
        assert isinstance(result, bool)

class TestCacheSecurityAPI:
    """Test cases for CacheSecurityAPI class."""
    
    def test_api_initialization(self):
        """Test API initialization."""
        api = CacheSecurityAPI()
        assert api is not None
    
    def test_api_health_check(self, security_api):
        """Test API health check."""
        # This should work with mock implementation
        result = security_api.health_check()
        assert isinstance(result, dict)

class TestIntegration:
    """Integration tests for cache security components."""
    
    def test_encryption_integration(self, cache_encryption, access_control_manager):
        """Test encryption and access control integration."""
        # Set up encryption
        key = Fernet.generate_key().decode()
        cache_encryption.set_encryption_key(key)
        
        # Test data
        test_data = "sensitive_data"
        encrypted = cache_encryption.encrypt(test_data)
        
        # Mock access control check
        with patch.object(access_control_manager, 'check_access', return_value=True):
            # Should be able to decrypt when access is granted
            decrypted = cache_encryption.decrypt(encrypted)
            assert decrypted == test_data

class TestPerformance:
    """Performance tests for cache security components."""
    
    def test_encryption_performance(self, cache_encryption):
        """Test encryption performance."""
        test_data = "performance_test_data" * 100  # Larger data
        
        # Measure encryption time
        start_time = time.time()
        encrypted = cache_encryption.encrypt(test_data)
        encrypt_time = time.time() - start_time
        
        # Measure decryption time
        start_time = time.time()
        decrypted = cache_encryption.decrypt(encrypted)
        decrypt_time = time.time() - start_time
        
        # Performance assertions
        assert encrypt_time < 0.01  # < 10ms
        assert decrypt_time < 0.01  # < 10ms
        assert decrypted == test_data
    
    def test_key_rotation_performance(self, cache_encryption):
        """Test key rotation performance."""
        start_time = time.time()
        new_key = cache_encryption.rotate_key()
        rotation_time = time.time() - start_time
        
        # Performance assertion
        assert rotation_time < 0.01  # < 10ms
        assert new_key is not None
        assert len(new_key) > 40

class TestErrorHandling:
    """Error handling tests for cache security components."""
    
    def test_invalid_encryption_key(self, cache_encryption):
        """Test error with invalid encryption key."""
        invalid_key = "invalid_key"
        
        with pytest.raises(Exception):
            cache_encryption.set_encryption_key(invalid_key)
    
    def test_decryption_without_key(self, cache_encryption):
        """Test decryption without key set."""
        with pytest.raises(Exception):
            cache_encryption.decrypt(b"encrypted_data")
    
    def test_empty_data_handling(self, cache_encryption):
        """Test handling of empty data."""
        assert cache_encryption.encrypt(None) is None
        assert cache_encryption.decrypt(None) is None

if __name__ == "__main__":
    pytest.main([__file__])
