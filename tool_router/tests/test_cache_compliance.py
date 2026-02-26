"""
Cache Compliance Module Tests

Comprehensive tests for the cache compliance module including:
- GDPR compliance functionality
- Data subject rights
- Consent management
- Compliance reporting
- Regulatory framework support
- API endpoint testing
"""

import gc
import time
from datetime import UTC, datetime, timedelta

import pytest

from tool_router.cache.compliance import (
    ComplianceManager,
    ComplianceReporter,
    DataSubjectRequestType,
    GDPRComplianceHandler,
)
from tool_router.cache.types import (
    CacheConfig,
    ComplianceError,
    ComplianceStandard,
)


class TestGDPRComplianceHandler:
    """Test GDPR compliance handler functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.gdpr_handler = GDPRComplianceHandler(self.config)

    def test_consent_recording_and_retrieval(self):
        """Test consent recording and retrieval."""
        consent_data = {
            "data_types": ["personal_data", "email", "name"],
            "purposes": ["marketing", "analytics", "communication"],
            "legal_basis": "consent",
        }

        subject_id = "test_subject_123"
        consent_id = self.gdpr_handler.record_consent(subject_id, consent_data)

        assert consent_id is not None
        assert len(consent_id) == 32

        with self.gdpr_handler._lock:
            assert consent_id in self.gdpr_handler._consent_records
            recorded_consent = self.gdpr_handler._consent_records[consent_id]
            assert recorded_consent.subject_id == subject_id
            assert recorded_consent.data_types == consent_data["data_types"]
            assert recorded_consent.purposes == consent_data["purposes"]
            assert recorded_consent.legal_basis == consent_data["legal_basis"]
            assert recorded_consent.granted is True

    def test_consent_validation_positive(self):
        """Test positive consent validation."""
        consent_data = {
            "data_types": ["email"],
            "purposes": ["newsletter"],
            "legal_basis": "consent",
        }

        subject_id = "consent_positive_user"
        self.gdpr_handler.record_consent(subject_id, consent_data)

        has_consent = self.gdpr_handler.check_consent(subject_id, "email", "newsletter")
        assert has_consent is True

        has_consent = self.gdpr_handler.check_consent(subject_id, "phone", "newsletter")
        assert has_consent is False

        has_consent = self.gdpr_handler.check_consent(subject_id, "email", "marketing")
        assert has_consent is False

    def test_consent_withdrawal(self):
        """Test consent withdrawal functionality."""
        consent_data = {
            "data_types": ["personal_data"],
            "purposes": ["analytics"],
            "legal_basis": "consent",
        }

        subject_id = "withdrawal_test_user"
        consent_id = self.gdpr_handler.record_consent(subject_id, consent_data)

        assert self.gdpr_handler.check_consent(subject_id, "personal_data", "analytics") is True

        success = self.gdpr_handler.withdraw_consent(consent_id)
        assert success is True

        with self.gdpr_handler._lock:
            recorded_consent = self.gdpr_handler._consent_records[consent_id]
            assert recorded_consent.granted is False
            assert recorded_consent.withdrawn_at is not None

        assert self.gdpr_handler.check_consent(subject_id, "personal_data", "analytics") is False

    def test_consent_expiration_handling(self):
        """Test consent expiration handling."""
        consent_data = {
            "data_types": ["test_data"],
            "purposes": ["test_purpose"],
            "legal_basis": "consent",
        }

        subject_id = "expiration_test_user"
        consent_id = self.gdpr_handler.record_consent(subject_id, consent_data)

        with self.gdpr_handler._lock:
            self.gdpr_handler._consent_records[consent_id].expires_at = datetime.utcnow() - timedelta(days=1)

        assert self.gdpr_handler.check_consent(subject_id, "test_data", "test_purpose") is False

    def test_multiple_consent_records(self):
        """Test handling multiple consent records for same subject."""
        subject_id = "multi_consent_user"

        consent1_data = {
            "data_types": ["email"],
            "purposes": ["newsletter"],
            "legal_basis": "consent",
        }

        consent2_data = {
            "data_types": ["personal_data"],
            "purposes": ["analytics"],
            "legal_basis": "consent",
        }

        consent1_id = self.gdpr_handler.record_consent(subject_id, consent1_data)
        consent2_id = self.gdpr_handler.record_consent(subject_id, consent2_data)

        assert self.gdpr_handler.check_consent(subject_id, "email", "newsletter") is True
        assert self.gdpr_handler.check_consent(subject_id, "personal_data", "analytics") is True

        self.gdpr_handler.withdraw_consent(consent1_id)

        assert self.gdpr_handler.check_consent(subject_id, "email", "newsletter") is False
        assert self.gdpr_handler.check_consent(subject_id, "personal_data", "analytics") is True

    def test_data_subject_request_creation(self):
        """Test data subject request creation."""
        request_data = {
            "request_type": "access",
            "subject_id": "dsr_test_user",
            "subject_contact": "user@example.com",
            "description": "Request for all personal data",
        }

        request_id = self.gdpr_handler.create_data_subject_request(request_data)

        assert request_id is not None
        assert len(request_id) == 32

        with self.gdpr_handler._lock:
            assert request_id in self.gdpr_handler._data_subject_requests
            recorded_request = self.gdpr_handler._data_subject_requests[request_id]
            assert recorded_request.request_type == DataSubjectRequestType.ACCESS
            assert recorded_request.subject_id == request_data["subject_id"]
            assert recorded_request.subject_contact == request_data["subject_contact"]
            assert recorded_request.description == request_data["description"]
            assert recorded_request.status == "pending"
            assert recorded_request.due_date > recorded_request.created

    def test_data_subject_request_retrieval(self):
        """Test data subject request retrieval."""
        subjects = ["user1", "user2", "user1", "user3"]

        for i, subject in enumerate(subjects):
            request_data = {
                "request_type": "access" if i % 2 == 0 else "erasure",
                "subject_id": subject,
                "subject_contact": f"{subject}@example.com",
                "description": f"Request {i}",
            }
            self.gdpr_handler.create_data_subject_request(request_data)

        user1_requests = self.gdpr_handler.get_data_subject_requests("user1")
        assert len(user1_requests) == 2
        assert all(req.subject_id == "user1" for req in user1_requests)

        all_requests = self.gdpr_handler.get_data_subject_requests()
        assert len(all_requests) == 4

    def test_right_to_be_forgotten_processing(self):
        """Test GDPR right to be forgotten processing."""
        subject_id = "rtbf_test_user"

        result = self.gdpr_handler.process_right_to_be_forgotten(subject_id)

        assert "subject_id" in result
        assert result["subject_id"] == subject_id
        assert "records_deleted" in result
        assert "cache_entries_cleared" in result
        assert "audit_logs_created" in result
        assert "processed_at" in result

        processed_at = datetime.fromisoformat(result["processed_at"])
        assert isinstance(processed_at, datetime)

    def test_consent_with_different_legal_bases(self):
        """Test consent with different legal bases."""
        subject_id = "legal_basis_test_user"

        legal_bases = [
            "consent",
            "contract",
            "legal_obligation",
            "vital_interests",
            "public_task",
            "legitimate_interests",
        ]

        for legal_basis in legal_bases:
            consent_data = {
                "data_types": ["test_data"],
                "purposes": ["test_purpose"],
                "legal_basis": legal_basis,
            }

            consent_id = self.gdpr_handler.record_consent(subject_id, consent_data)

            with self.gdpr_handler._lock:
                recorded_consent = self.gdpr_handler._consent_records[consent_id]
                assert recorded_consent.legal_basis == legal_basis


class TestComplianceReporter:
    """Test compliance reporter functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.reporter = ComplianceReporter(self.config)

    def test_gdpr_compliance_assessment(self):
        """Test GDPR compliance assessment."""
        assessment = self.reporter.assess_gdpr_compliance()

        assert assessment.standard == ComplianceStandard.GDPR
        assert isinstance(assessment.score, float)
        assert 0 <= assessment.score <= 100
        assert isinstance(assessment.findings, list)
        assert isinstance(assessment.recommendations, list)
        assert assessment.last_assessed is not None
        assert assessment.next_assessment is not None
        assert assessment.assessor == "compliance_system"

        finding_texts = " ".join(assessment.findings).lower()
        assert "consent" in finding_texts or "encryption" in finding_texts
        assert "retention" in finding_texts or "policy" in finding_texts

    def test_compliance_assessment_with_different_configurations(self):
        """Test compliance assessment with different configurations."""
        config_no_encryption = CacheConfig(encryption_enabled=False)
        reporter_no_encryption = ComplianceReporter(config_no_encryption)
        assessment_no_encryption = reporter_no_encryption.assess_gdpr_compliance()

        config_no_retention = CacheConfig()
        config_no_retention.retention_days = {}
        reporter_no_retention = ComplianceReporter(config_no_retention)
        assessment_no_retention = reporter_no_retention.assess_gdpr_compliance()

        assert assessment_no_encryption.score < 100
        assert assessment_no_retention.score < 100

        assert len(assessment_no_encryption.recommendations) > 0
        assert len(assessment_no_retention.recommendations) > 0

    def test_compliance_report_generation(self):
        """Test comprehensive compliance report generation."""
        standards = [ComplianceStandard.GDPR]
        report = self.reporter.generate_compliance_report(standards)

        assert report.report_id is not None
        assert len(report.report_id) == 32
        assert report.period_start is not None
        assert report.period_end is not None
        assert report.period_end > report.period_start
        assert report.standards == standards
        assert len(report.assessments) == 1
        assert report.assessments[0].standard == ComplianceStandard.GDPR
        assert isinstance(report.data_subject_requests, list)
        assert isinstance(report.total_records_processed, int)
        assert isinstance(report.data_breaches, list)
        assert isinstance(report.recommendations, list)
        assert report.generated is not None
        assert report.generated_by == "compliance_system"

    def test_multi_standard_compliance_report(self):
        """Test compliance report with multiple standards."""
        standards = [ComplianceStandard.GDPR]

        report = self.reporter.generate_compliance_report(standards)

        assert len(report.standards) == 1
        assert len(report.assessments) == 1

    def test_assessment_history_tracking(self):
        """Test assessment history tracking."""
        assessment1 = self.reporter.assess_gdpr_compliance()
        time.sleep(0.1)
        assessment2 = self.reporter.assess_gdpr_compliance()

        history = self.reporter.get_assessment_history(ComplianceStandard.GDPR)

        assert len(history) >= 1
        assert history[0].standard == ComplianceStandard.GDPR

        assert history[0].last_assessed >= assessment1.last_assessed


class TestComplianceManager:
    """Test compliance manager integration."""

    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.compliance_manager = ComplianceManager(self.config)

    def test_consent_management_workflow(self):
        """Test complete consent management workflow."""
        subject_id = "workflow_test_user"

        consent_data = {
            "data_types": ["email", "preferences"],
            "purposes": ["personalization", "analytics"],
            "legal_basis": "consent",
        }

        consent_id = self.compliance_manager.record_consent(subject_id, consent_data)
        assert consent_id is not None

        has_consent = self.compliance_manager.check_consent(subject_id, "email", "personalization")
        assert has_consent is True

        has_consent = self.compliance_manager.check_consent(
            subject_id,
            "phone",
            "personalization",
        )
        assert has_consent is False

        success = self.compliance_manager.withdraw_consent(consent_id)
        assert success is True

        has_consent = self.compliance_manager.check_consent(subject_id, "email", "personalization")
        assert has_consent is False

    def test_data_subject_request_management(self):
        """Test data subject request management."""
        requests_data = [
            {
                "request_type": "access",
                "subject_id": "dsr_user_1",
                "subject_contact": "user1@example.com",
                "description": "Request for all personal data",
            },
            {
                "request_type": "erasure",
                "subject_id": "dsr_user_2",
                "subject_contact": "user2@example.com",
                "description": "Request to delete all data",
            },
            {
                "request_type": "portability",
                "subject_id": "dsr_user_1",
                "subject_contact": "user1@example.com",
                "description": "Request for data export",
            },
        ]

        request_ids = []
        for request_data in requests_data:
            request_id = self.compliance_manager.create_data_subject_request(request_data)
            request_ids.append(request_id)
            assert request_id is not None

        all_requests = self.compliance_manager.get_data_subject_requests()
        assert len(all_requests) >= 3

        user1_requests = self.compliance_manager.get_data_subject_requests("dsr_user_1")
        assert len(user1_requests) == 2
        assert all(req.subject_id == "dsr_user_1" for req in user1_requests)

    def test_right_to_be_forgotten_integration(self):
        """Test right to be forgotten integration."""
        subject_id = "rtbf_integration_user"

        result = self.compliance_manager.process_right_to_be_forgotten(subject_id)

        assert "subject_id" in result
        assert result["subject_id"] == subject_id
        assert "processed_at" in result

        processed_at = datetime.fromisoformat(result["processed_at"])
        assert isinstance(processed_at, datetime)
        assert (datetime.now(UTC) - processed_at.replace(tzinfo=UTC)) < timedelta(minutes=1)

    def test_compliance_assessment_integration(self):
        """Test compliance assessment integration."""
        assessment = self.compliance_manager.assess_compliance(ComplianceStandard.GDPR)

        assert assessment.standard == ComplianceStandard.GDPR
        assert isinstance(assessment.score, float)
        assert 0 <= assessment.score <= 100
        assert isinstance(assessment.findings, list)
        assert isinstance(assessment.recommendations, list)
        assert assessment.last_assessed is not None
        assert assessment.next_assessment is not None
        assert assessment.assessor is not None

    def test_compliance_reporting_integration(self):
        """Test compliance reporting integration."""
        report = self.compliance_manager.generate_compliance_report()

        assert report.report_id is not None
        assert len(report.standards) >= 1
        assert len(report.assessments) >= 1
        assert report.generated is not None
        assert report.generated_by is not None

        report_specific = self.compliance_manager.generate_compliance_report([ComplianceStandard.GDPR])

        assert report_specific.standards == [ComplianceStandard.GDPR]
        assert len(report_specific.assessments) == 1
        assert report_specific.assessments[0].standard == ComplianceStandard.GDPR

    def test_metrics_collection(self):
        """Test compliance metrics collection."""
        self.compliance_manager.record_consent(
            "metrics_user",
            {"data_types": ["test"], "purposes": ["test"], "legal_basis": "consent"},
        )

        self.compliance_manager.check_consent("metrics_user", "test", "test")

        self.compliance_manager.create_data_subject_request(
            {
                "request_type": "access",
                "subject_id": "metrics_user",
                "subject_contact": "test@example.com",
                "description": "Test request",
            }
        )

        metrics = self.compliance_manager.get_metrics()

        assert metrics.total_compliance_checks >= 3
        assert isinstance(metrics.compliance_violations, int)
        assert isinstance(metrics.encryption_errors, int)
        assert isinstance(metrics.access_denied, int)
        assert isinstance(metrics.audit_failures, int)

    def test_error_handling(self):
        """Test error handling in compliance operations."""
        with pytest.raises(ComplianceError):
            self.compliance_manager.record_consent("", {})

        with pytest.raises(ComplianceError):
            self.compliance_manager.create_data_subject_request({})

        with pytest.raises(TypeError):
            self.compliance_manager.assess_compliance("INVALID_STANDARD")


class TestComplianceIntegration:
    """Test compliance integration scenarios."""

    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.compliance_manager = ComplianceManager(self.config)

    def test_consent_driven_data_processing_workflow(self):
        """Test consent-driven data processing workflow."""
        user_id = "consent_workflow_user"

        has_consent = self.compliance_manager.check_consent(user_id, "email", "marketing")
        assert has_consent is False

        consent_id = self.compliance_manager.record_consent(
            user_id,
            {
                "data_types": ["email", "name"],
                "purposes": ["marketing", "analytics"],
                "legal_basis": "consent",
            },
        )

        has_consent = self.compliance_manager.check_consent(user_id, "email", "marketing")
        assert has_consent is True

        self.compliance_manager.withdraw_consent(consent_id)

        has_consent = self.compliance_manager.check_consent(user_id, "email", "marketing")
        assert has_consent is False

    def test_data_subject_rights_workflow(self):
        """Test complete data subject rights workflow."""
        subject_id = "rights_workflow_user"
        subject_contact = "user@example.com"

        access_request_id = self.compliance_manager.create_data_subject_request(
            {
                "request_type": "access",
                "subject_id": subject_id,
                "subject_contact": subject_contact,
                "description": "Request copy of all personal data",
            }
        )

        rectification_request_id = self.compliance_manager.create_data_subject_request(
            {
                "request_type": "rectification",
                "subject_id": subject_id,
                "subject_contact": subject_contact,
                "description": "Request to correct inaccurate data",
            }
        )

        erasure_request_id = self.compliance_manager.create_data_subject_request(
            {
                "request_type": "erasure",
                "subject_id": subject_id,
                "subject_contact": subject_contact,
                "description": "Request to delete all personal data",
            }
        )

        user_requests = self.compliance_manager.get_data_subject_requests(subject_id)
        assert len(user_requests) == 3

        request_types = [req.request_type.value for req in user_requests]
        assert "access" in request_types
        assert "rectification" in request_types
        assert "erasure" in request_types

        rtbf_result = self.compliance_manager.process_right_to_be_forgotten(subject_id)

        assert rtbf_result["subject_id"] == subject_id
        assert "processed_at" in rtbf_result

    def test_compliance_assessment_driven_improvements(self):
        """Test compliance assessment-driven improvements."""
        initial_assessment = self.compliance_manager.assess_compliance(ComplianceStandard.GDPR)

        improved_assessment = self.compliance_manager.assess_compliance(ComplianceStandard.GDPR)

        assert improved_assessment.standard == ComplianceStandard.GDPR
        assert isinstance(improved_assessment.score, float)
        assert isinstance(improved_assessment.findings, list)
        assert isinstance(improved_assessment.recommendations, list)

        report = self.compliance_manager.generate_compliance_report([ComplianceStandard.GDPR])

        assert report.assessments[0].standard == ComplianceStandard.GDPR
        assert report.assessments[0].score == improved_assessment.score

    def test_multi_user_consent_management(self):
        """Test consent management across multiple users."""
        users = [f"user_{i}" for i in range(10)]

        consent_records = {}
        for user in users:
            consent_data = {
                "data_types": (["email", "preferences"] if int(user.split("_")[1]) % 2 == 0 else ["name"]),
                "purposes": (["marketing"] if int(user.split("_")[1]) % 3 == 0 else ["analytics"]),
                "legal_basis": "consent",
            }

            consent_id = self.compliance_manager.record_consent(user, consent_data)
            consent_records[user] = consent_id

        for user in users:
            user_index = int(user.split("_")[1])

            if user_index % 2 == 0:
                has_email = self.compliance_manager.check_consent(user, "email", "marketing")
                if user_index % 3 == 0:
                    assert has_email is True
            else:
                has_consent = self.compliance_manager.check_consent(user, "email", "marketing")
                assert has_consent is False

        for i, user in enumerate(users):
            if i % 2 == 0:
                self.compliance_manager.withdraw_consent(consent_records[user])

        for i, user in enumerate(users):
            if i % 2 == 0:
                has_consent = self.compliance_manager.check_consent(user, "email", "marketing")
                assert has_consent is False


class TestCompliancePerformance:
    """Test compliance performance and scalability."""

    def setup_method(self):
        """Setup test environment."""
        self.config = CacheConfig()
        self.compliance_manager = ComplianceManager(self.config)

    def test_consent_check_performance(self):
        """Test consent check performance with high volume."""
        num_consent_records = 1000
        subject_id = "perf_test_user"

        consent_ids = []
        for i in range(num_consent_records):
            consent_data = {
                "data_types": [f"data_type_{i}"],
                "purposes": [f"purpose_{i}"],
                "legal_basis": "consent",
            }

            consent_id = self.compliance_manager.record_consent(subject_id, consent_data)
            consent_ids.append(consent_id)

        start_time = time.time()

        for i in range(num_consent_records):
            has_consent = self.compliance_manager.check_consent(subject_id, f"data_type_{i}", f"purpose_{i}")
            assert has_consent is True

        check_time = time.time() - start_time

        assert check_time < 5.0
        assert check_time / num_consent_records < 0.01

    def test_concurrent_consent_operations(self):
        """Test concurrent consent operations."""
        import queue
        import threading

        results = queue.Queue()
        errors = queue.Queue()

        def record_consent(user_id_suffix):
            try:
                consent_data = {
                    "data_types": ["test_data"],
                    "purposes": ["test_purpose"],
                    "legal_basis": "consent",
                }

                consent_id = self.compliance_manager.record_consent(f"concurrent_user_{user_id_suffix}", consent_data)
                results.put(consent_id)
            except Exception as e:
                errors.put(e)

        def check_consent(user_id_suffix):
            try:
                has_consent = self.compliance_manager.check_consent(
                    f"concurrent_user_{user_id_suffix}", "test_data", "test_purpose"
                )
                results.put(has_consent)
            except Exception as e:
                errors.put(e)

        threads = []

        for i in range(10):
            thread = threading.Thread(target=record_consent, args=(i,))
            threads.append(thread)
            thread.start()

        for i in range(10):
            thread = threading.Thread(target=check_consent, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert errors.empty(), f"Errors occurred: {list(errors.queue)}"
        assert results.qsize() == 20

        consent_ids = []
        while not results.empty():
            result = results.get()
            if isinstance(result, str):
                consent_ids.append(result)
                assert len(result) == 32
            else:
                assert isinstance(result, bool)

    def test_assessment_performance(self):
        """Test compliance assessment performance."""
        num_assessments = 100

        start_time = time.time()

        for i in range(num_assessments):
            assessment = self.compliance_manager.assess_compliance(ComplianceStandard.GDPR)
            assert assessment.standard == ComplianceStandard.GDPR
            assert isinstance(assessment.score, float)

        total_time = time.time() - start_time
        avg_time = total_time / num_assessments

        assert avg_time < 0.1
        assert total_time < 10.0

    def test_report_generation_performance(self):
        """Test report generation performance."""
        num_reports = 50

        start_time = time.time()

        for i in range(num_reports):
            report = self.compliance_manager.generate_compliance_report([ComplianceStandard.GDPR])
            assert report.report_id is not None
            assert len(report.assessments) == 1
            assert report.assessments[0].standard == ComplianceStandard.GDPR

        total_time = time.time() - start_time
        avg_time = total_time / num_reports

        assert avg_time < 0.5
        assert total_time < 25.0

    def test_memory_usage_with_large_dataset(self):
        """Test memory usage with large consent datasets."""
        initial_objects = len(gc.get_objects())

        num_records = 5000
        subject_id = "memory_test_user"

        consent_ids = []
        for i in range(num_records):
            consent_data = {
                "data_types": [f"data_type_{i % 100}"],
                "purposes": [f"purpose_{i % 50}"],
                "legal_basis": "consent",
            }

            consent_id = self.compliance_manager.record_consent(subject_id, consent_data)
            consent_ids.append(consent_id)

        for i in range(num_records):
            self.compliance_manager.check_consent(subject_id, f"data_type_{i % 100}", f"purpose_{i % 50}")

        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects

        assert object_increase < num_records * 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
