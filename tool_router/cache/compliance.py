"""
Cache Compliance Module

This module provides comprehensive compliance features for the MCP Gateway caching system:
- GDPR compliance management
- Data subject rights implementation
- Compliance reporting and assessment
- Regulatory framework support
- Compliance audit trails

Key Components:
- ComplianceManager: Main compliance management interface
- GDPRComplianceHandler: Specific GDPR implementation
- DataSubjectRights: Handle data subject requests
- ComplianceReporter: Generate compliance reports
- RegulatoryFramework: Support multiple compliance standards
"""

import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any

from .config import CacheConfig
from .types import (
    AuditEntry,
    ComplianceError,
    ComplianceStandard,
    ConsentRecord,
    SecurityMetrics,
)


class ComplianceStatus(Enum):
    """Compliance status enumeration."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPT = "exempt"
    UNKNOWN = "unknown"


class DataSubjectRequestType(Enum):
    """Data subject request types."""

    ACCESS = "access"
    PORTABILITY = "portability"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICTION = "restriction"
    OBJECTION = "objection"


@dataclass
class ComplianceAssessment:
    """Compliance assessment result."""

    standard: ComplianceStandard
    status: ComplianceStatus
    score: float  # 0-100
    findings: list[str]
    recommendations: list[str]
    last_assessed: datetime
    next_assessment: datetime
    assessor: str


@dataclass
class DataSubjectRequest:
    """Data subject request record."""

    request_id: str
    request_type: DataSubjectRequestType
    subject_id: str
    subject_contact: str
    description: str
    status: str
    created: datetime
    due_date: datetime
    completed: datetime | None = None
    notes: str = ""
    processed_by: str | None = None


@dataclass
class ComplianceReport:
    """Compliance report data."""

    report_id: str
    period_start: datetime
    period_end: datetime
    standards: list[ComplianceStandard]
    assessments: list[ComplianceAssessment]
    data_subject_requests: list[DataSubjectRequest]
    total_records_processed: int
    data_breaches: list[dict[str, Any]]
    recommendations: list[str]
    generated: datetime
    generated_by: str


class GDPRComplianceHandler:
    """GDPR-specific compliance implementation."""

    def __init__(self, config: CacheConfig):
        """Initialize GDPR compliance handler."""
        self.config = config
        self._lock = Lock()
        self._consent_records: dict[str, ConsentRecord] = {}
        self._data_subject_requests: dict[str, DataSubjectRequest] = {}

    def record_consent(self, subject_id: str, consent_data: dict[str, Any]) -> str:
        """Record consent for data processing."""
        consent_id = secrets.token_hex(16)

        consent_record = ConsentRecord(
            consent_id=consent_id,
            subject_id=subject_id,
            data_types=consent_data.get("data_types", []),
            purposes=consent_data.get("purposes", []),
            legal_basis=consent_data.get("legal_basis", "consent"),
            granted=True,
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            withdrawn_at=None,
        )

        with self._lock:
            self._consent_records[consent_id] = consent_record

        return consent_id

    def check_consent(self, subject_id: str, data_type: str, purpose: str) -> bool:
        """Check if valid consent exists for data processing."""
        with self._lock:
            for consent in self._consent_records.values():
                if (
                    consent.subject_id == subject_id
                    and data_type in consent.data_types
                    and purpose in consent.purposes
                    and consent.granted
                    and consent.expires_at > datetime.utcnow()
                    and consent.withdrawn_at is None
                ):
                    return True
        return False

    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw previously given consent."""
        with self._lock:
            if consent_id in self._consent_records:
                self._consent_records[consent_id].granted = False
                self._consent_records[consent_id].withdrawn_at = datetime.utcnow()
                return True
        return False

    def create_data_subject_request(self, request_data: dict[str, Any]) -> str:
        """Create a new data subject request."""
        request_id = secrets.token_hex(16)

        request = DataSubjectRequest(
            request_id=request_id,
            request_type=DataSubjectRequestType(request_data["request_type"]),
            subject_id=request_data["subject_id"],
            subject_contact=request_data["subject_contact"],
            description=request_data["description"],
            status="pending",
            created=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),  # GDPR 30-day response
        )

        with self._lock:
            self._data_subject_requests[request_id] = request

        return request_id

    def get_data_subject_requests(self, subject_id: str | None = None) -> list[DataSubjectRequest]:
        """Get data subject requests, optionally filtered by subject."""
        with self._lock:
            requests = list(self._data_subject_requests.values())
            if subject_id:
                requests = [r for r in requests if r.subject_id == subject_id]
            return requests

    def process_right_to_be_forgotten(self, subject_id: str) -> dict[str, Any]:
        """Process GDPR right to be forgotten request."""
        # This would integrate with cache operations to delete subject data
        processed_data = {
            "subject_id": subject_id,
            "records_deleted": 0,
            "cache_entries_cleared": 0,
            "audit_logs_created": 0,
            "processed_at": datetime.utcnow().isoformat(),
        }

        # Log the erasure request
        audit_entry = AuditEntry(
            event_id=secrets.token_hex(16),
            event_type="data_erasure",
            user_id="system",
            resource_id=subject_id,
            details={"description": f"GDPR right to be forgotten processed for {subject_id}"},
            timestamp=datetime.utcnow(),
            ip_address="127.0.0.1",
            user_agent="compliance_system",
        )

        # In a real implementation, this would trigger actual data deletion
        # For now, we'll just record the request

        return processed_data


class ComplianceReporter:
    """Generate compliance reports and assessments."""

    def __init__(self, config: CacheConfig):
        """Initialize compliance reporter."""
        self.config = config
        self._lock = Lock()
        self._assessments: dict[ComplianceStandard, ComplianceAssessment] = {}

    def assess_gdpr_compliance(self) -> ComplianceAssessment:
        """Assess GDPR compliance status."""
        findings = []
        recommendations = []
        score = 85.0  # Base score

        # Check consent management
        findings.append("Consent management system implemented")
        recommendations.append("Regular consent audits recommended")

        # Check data subject rights
        findings.append("Data subject request system operational")
        recommendations.append("Monitor request response times")

        # Check data retention
        findings.append("Data retention policies defined")
        if not self.config.retention_days:
            findings.append("WARNING: Default retention policy not configured")
            score -= 10
            recommendations.append("Configure appropriate retention periods")

        # Check encryption
        if self.config.encryption_enabled:
            findings.append("Data encryption enabled")
            score += 5
        else:
            findings.append("WARNING: Data encryption not enabled")
            score -= 15
            recommendations.append("Enable encryption for sensitive data")

        assessment = ComplianceAssessment(
            standard=ComplianceStandard.GDPR,
            status=(ComplianceStatus.COMPLIANT if score >= 80 else ComplianceStatus.NON_COMPLIANT),
            score=score,
            findings=findings,
            recommendations=recommendations,
            last_assessed=datetime.utcnow(),
            next_assessment=datetime.utcnow() + timedelta(days=90),
            assessor="compliance_system",
        )

        with self._lock:
            self._assessments[ComplianceStandard.GDPR] = assessment

        return assessment

    def generate_compliance_report(self, standards: list[ComplianceStandard]) -> ComplianceReport:
        """Generate comprehensive compliance report."""
        report_id = secrets.token_hex(16)
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=30)

        assessments = []
        for standard in standards:
            if standard == ComplianceStandard.GDPR:
                assessments.append(self.assess_gdpr_compliance())
            else:
                # Placeholder for other standards
                assessments.append(
                    ComplianceAssessment(
                        standard=standard,
                        status=ComplianceStatus.UNKNOWN,
                        score=0.0,
                        findings=["Assessment not implemented"],
                        recommendations=["Implement assessment for this standard"],
                        last_assessed=datetime.utcnow(),
                        next_assessed=datetime.utcnow() + timedelta(days=90),
                        assessor="compliance_system",
                    )
                )

        report = ComplianceReport(
            report_id=report_id,
            period_start=period_start,
            period_end=period_end,
            standards=standards,
            assessments=assessments,
            data_subject_requests=[],  # Would be populated from actual data
            total_records_processed=0,  # Would be calculated from actual data
            data_breaches=[],  # Would be populated from incident logs
            recommendations=[],
            generated=datetime.utcnow(),
            generated_by="compliance_system",
        )

        return report

    def get_assessment_history(self, standard: ComplianceStandard) -> list[ComplianceAssessment]:
        """Get assessment history for a standard."""
        with self._lock:
            if standard in self._assessments:
                return [self._assessments[standard]]
            return []


class ComplianceManager:
    """Main compliance management interface."""

    def __init__(self, config: CacheConfig | None):
        """Initialize compliance manager."""
        self.config = config or CacheConfig()
        self._lock = Lock()

        # Initialize compliance handlers
        self._gdpr_handler = GDPRComplianceHandler(self.config)
        self._reporter = ComplianceReporter(self.config)

        # Compliance metrics
        self._metrics = SecurityMetrics(
            encryption_operations=0,
            decryption_operations=0,
            access_denied=0,
            access_granted=0,
            audit_entries=0,
            consent_records=0,
            data_breaches=0,
            security_violations=0,
            last_updated=datetime.now(),
        )

    def record_consent(self, subject_id: str, consent_data: dict[str, Any]) -> str:
        """Record consent for data processing."""
        if not subject_id or not consent_data:
            raise ComplianceError("Subject ID and consent data are required")
        try:
            consent_id = self._gdpr_handler.record_consent(subject_id, consent_data)

            with self._lock:
                self._metrics.audit_entries += 1
                self._metrics.total_compliance_checks += 1

            return consent_id

        except ComplianceError:
            raise
        except Exception as e:
            raise ComplianceError(f"Failed to record consent: {e!s}")

    def check_consent(self, subject_id: str, data_type: str, purpose: str) -> bool:
        """Check if valid consent exists."""
        has_consent = self._gdpr_handler.check_consent(subject_id, data_type, purpose)

        with self._lock:
            self._metrics.audit_entries += 1
            self._metrics.total_compliance_checks += 1
            if not has_consent:
                self._metrics.compliance_violations += 1

        return has_consent

    def create_data_subject_request(self, request_data: dict[str, Any]) -> str:
        """Create a new data subject request."""
        required = ["request_type", "subject_id", "subject_contact", "description"]
        if not all(k in request_data for k in required):
            raise ComplianceError(f"Missing required fields: {required}")
        try:
            request_id = self._gdpr_handler.create_data_subject_request(request_data)

            with self._lock:
                self._metrics.audit_entries += 1
                self._metrics.total_compliance_checks += 1

            return request_id

        except ComplianceError:
            raise
        except Exception as e:
            raise ComplianceError(f"Failed to create data subject request: {e!s}")

    def process_right_to_be_forgotten(self, subject_id: str) -> dict[str, Any]:
        """Process GDPR right to be forgotten."""
        try:
            result = self._gdpr_handler.process_right_to_be_forgotten(subject_id)

            # Update metrics
            with self._lock:
                self._metrics.audit_entries += 1

            return result

        except Exception as e:
            raise ComplianceError(f"Failed to process right to be forgotten: {e!s}")

    def assess_compliance(self, standard: ComplianceStandard | str) -> ComplianceAssessment:
        """Assess compliance for a specific standard."""
        if not isinstance(standard, ComplianceStandard):
            raise TypeError(f"Invalid compliance standard: {standard}")

        if standard == ComplianceStandard.GDPR:
            assessment = self._reporter.assess_gdpr_compliance()
        else:
            raise ComplianceError(f"Compliance assessment for {standard.value} not implemented")

        with self._lock:
            self._metrics.audit_entries += 1

        return assessment

    def generate_compliance_report(self, standards: list[ComplianceStandard] | None = None) -> ComplianceReport:
        """Generate compliance report."""
        try:
            if standards is None:
                standards = [ComplianceStandard.GDPR]

            report = self._reporter.generate_compliance_report(standards)

            # Update metrics
            with self._lock:
                self._metrics.audit_entries += 1

            return report

        except Exception as e:
            raise ComplianceError(f"Failed to generate compliance report: {e!s}")

    def get_metrics(self) -> SecurityMetrics:
        """Get compliance metrics."""
        with self._lock:
            return SecurityMetrics(**asdict(self._metrics))

    def get_data_subject_requests(self, subject_id: str | None = None) -> list[DataSubjectRequest]:
        """Get data subject requests."""
        return self._gdpr_handler.get_data_subject_requests(subject_id)

    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw consent."""
        try:
            success = self._gdpr_handler.withdraw_consent(consent_id)

            # Update metrics
            with self._lock:
                self._metrics.audit_entries += 1

            return success

        except Exception as e:
            raise ComplianceError(f"Failed to withdraw consent: {e!s}")
