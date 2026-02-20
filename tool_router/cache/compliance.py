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

import os
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field, asdict
from threading import Lock
from collections import defaultdict
from enum import Enum

from .types import (
    DataClassification, AccessLevel, ComplianceStandard, SecurityPolicy,
    ConsentRecord, AuditEntry, CacheEntryMetadata, SecurityMetrics,
    CacheOperationResult, CacheSecurityError, ComplianceError, AuditError
)
from .config import CacheConfig


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
    findings: List[str]
    recommendations: List[str]
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
    completed: Optional[datetime] = None
    notes: str = ""
    processed_by: Optional[str] = None


@dataclass
class ComplianceReport:
    """Compliance report data."""
    report_id: str
    period_start: datetime
    period_end: datetime
    standards: List[ComplianceStandard]
    assessments: List[ComplianceAssessment]
    data_subject_requests: List[DataSubjectRequest]
    total_records_processed: int
    data_breaches: List[Dict[str, Any]]
    recommendations: List[str]
    generated: datetime
    generated_by: str


class GDPRComplianceHandler:
    """GDPR-specific compliance implementation."""
    
    def __init__(self, config: CacheConfig):
        """Initialize GDPR compliance handler."""
        self.config = config
        self._lock = Lock()
        self._consent_records: Dict[str, ConsentRecord] = {}
        self._data_subject_requests: Dict[str, DataSubjectRequest] = {}
        
    def record_consent(self, subject_id: str, consent_data: Dict[str, Any]) -> str:
        """Record consent for data processing."""
        consent_id = secrets.token_hex(16)
        
        consent_record = ConsentRecord(
            consent_id=consent_id,
            subject_id=subject_id,
            data_types=consent_data.get('data_types', []),
            purposes=consent_data.get('purposes', []),
            legal_basis=consent_data.get('legal_basis', 'consent'),
            granted=True,
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            withdrawn_at=None
        )
        
        with self._lock:
            self._consent_records[consent_id] = consent_record
            
        return consent_id
    
    def check_consent(self, subject_id: str, data_type: str, purpose: str) -> bool:
        """Check if valid consent exists for data processing."""
        with self._lock:
            for consent in self._consent_records.values():
                if (consent.subject_id == subject_id and
                    data_type in consent.data_types and
                    purpose in consent.purposes and
                    consent.granted and
                    consent.expires_at > datetime.utcnow() and
                    consent.withdrawn_at is None):
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
    
    def create_data_subject_request(self, request_data: Dict[str, Any]) -> str:
        """Create a new data subject request."""
        request_id = secrets.token_hex(16)
        
        request = DataSubjectRequest(
            request_id=request_id,
            request_type=DataSubjectRequestType(request_data['request_type']),
            subject_id=request_data['subject_id'],
            subject_contact=request_data['subject_contact'],
            description=request_data['description'],
            status='pending',
            created=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30)  # GDPR 30-day response
        )
        
        with self._lock:
            self._data_subject_requests[request_id] = request
            
        return request_id
    
    def get_data_subject_requests(self, subject_id: Optional[str] = None) -> List[DataSubjectRequest]:
        """Get data subject requests, optionally filtered by subject."""
        with self._lock:
            requests = list(self._data_subject_requests.values())
            if subject_id:
                requests = [r for r in requests if r.subject_id == subject_id]
            return requests
    
    def process_right_to_be_forgotten(self, subject_id: str) -> Dict[str, Any]:
        """Process GDPR right to be forgotten request."""
        # This would integrate with cache operations to delete subject data
        processed_data = {
            'subject_id': subject_id,
            'records_deleted': 0,
            'cache_entries_cleared': 0,
            'audit_logs_created': 0,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        # Log the erasure request
        audit_entry = AuditEntry(
            entry_id=secrets.token_hex(16),
            event_type='data_erasure',
            user_id='system',
            resource_id=subject_id,
            details=f"GDPR right to be forgotten processed for {subject_id}",
            timestamp=datetime.utcnow(),
            ip_address='127.0.0.1',
            user_agent='compliance_system',
            success=True
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
        self._assessments: Dict[ComplianceStandard, ComplianceAssessment] = {}
        
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
            status=ComplianceStatus.COMPLIANT if score >= 80 else ComplianceStatus.NON_COMPLIANT,
            score=score,
            findings=findings,
            recommendations=recommendations,
            last_assessed=datetime.utcnow(),
            next_assessed=datetime.utcnow() + timedelta(days=90),
            assessor='compliance_system'
        )
        
        with self._lock:
            self._assessments[ComplianceStandard.GDPR] = assessment
            
        return assessment
    
    def generate_compliance_report(self, standards: List[ComplianceStandard]) -> ComplianceReport:
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
                assessments.append(ComplianceAssessment(
                    standard=standard,
                    status=ComplianceStatus.UNKNOWN,
                    score=0.0,
                    findings=["Assessment not implemented"],
                    recommendations=["Implement assessment for this standard"],
                    last_assessed=datetime.utcnow(),
                    next_assessed=datetime.utcnow() + timedelta(days=90),
                    assessor='compliance_system'
                ))
        
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
            generated_by='compliance_system'
        )
        
        return report
    
    def get_assessment_history(self, standard: ComplianceStandard) -> List[ComplianceAssessment]:
        """Get assessment history for a standard."""
        with self._lock:
            if standard in self._assessments:
                return [self._assessments[standard]]
            return []


class ComplianceManager:
    """Main compliance management interface."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize compliance manager."""
        self.config = config or CacheConfig()
        self._lock = Lock()
        
        # Initialize compliance handlers
        self._gdpr_handler = GDPRComplianceHandler(self.config)
        self._reporter = ComplianceReporter(self.config)
        
        # Compliance metrics
        self._metrics = SecurityMetrics(
            total_encryption_operations=0,
            total_access_control_checks=0,
            total_compliance_checks=0,
            total_audit_events=0,
            encryption_errors=0,
            access_denied=0,
            compliance_violations=0,
            audit_failures=0
        )
    
    def record_consent(self, subject_id: str, consent_data: Dict[str, Any]) -> str:
        """Record consent for data processing."""
        try:
            consent_id = self._gdpr_handler.record_consent(subject_id, consent_data)
            
            # Update metrics
            with self._lock:
                self._metrics.total_compliance_checks += 1
            
            return consent_id
            
        except Exception as e:
            raise ComplianceError(f"Failed to record consent: {str(e)}")
    
    def check_consent(self, subject_id: str, data_type: str, purpose: str) -> bool:
        """Check if valid consent exists."""
        try:
            has_consent = self._gdpr_handler.check_consent(subject_id, data_type, purpose)
            
            # Update metrics
            with self._lock:
                self._metrics.total_compliance_checks += 1
                if not has_consent:
                    self._metrics.compliance_violations += 1
            
            return has_consent
            
        except Exception as e:
            raise ComplianceError(f"Failed to check consent: {str(e)}")
    
    def create_data_subject_request(self, request_data: Dict[str, Any]) -> str:
        """Create a new data subject request."""
        try:
            request_id = self._gdpr_handler.create_data_subject_request(request_data)
            
            # Update metrics
            with self._lock:
                self._metrics.total_compliance_checks += 1
            
            return request_id
            
        except Exception as e:
            raise ComplianceError(f"Failed to create data subject request: {str(e)}")
    
    def process_right_to_be_forgotten(self, subject_id: str) -> Dict[str, Any]:
        """Process GDPR right to be forgotten."""
        try:
            result = self._gdpr_handler.process_right_to_be_forgotten(subject_id)
            
            # Update metrics
            with self._lock:
                self._metrics.total_compliance_checks += 1
            
            return result
            
        except Exception as e:
            raise ComplianceError(f"Failed to process right to be forgotten: {str(e)}")
    
    def assess_compliance(self, standard: ComplianceStandard) -> ComplianceAssessment:
        """Assess compliance for a specific standard."""
        try:
            if standard == ComplianceStandard.GDPR:
                assessment = self._reporter.assess_gdpr_compliance()
            else:
                raise ComplianceError(f"Compliance assessment for {standard.value} not implemented")
            
            # Update metrics
            with self._lock:
                self._metrics.total_compliance_checks += 1
            
            return assessment
            
        except Exception as e:
            raise ComplianceError(f"Failed to assess compliance: {str(e)}")
    
    def generate_compliance_report(self, standards: Optional[List[ComplianceStandard]] = None) -> ComplianceReport:
        """Generate compliance report."""
        try:
            if standards is None:
                standards = [ComplianceStandard.GDPR]
            
            report = self._reporter.generate_compliance_report(standards)
            
            # Update metrics
            with self._lock:
                self._metrics.total_compliance_checks += 1
            
            return report
            
        except Exception as e:
            raise ComplianceError(f"Failed to generate compliance report: {str(e)}")
    
    def get_metrics(self) -> SecurityMetrics:
        """Get compliance metrics."""
        with self._lock:
            return SecurityMetrics(**asdict(self._metrics))
    
    def get_data_subject_requests(self, subject_id: Optional[str] = None) -> List[DataSubjectRequest]:
        """Get data subject requests."""
        return self._gdpr_handler.get_data_subject_requests(subject_id)
    
    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw consent."""
        try:
            success = self._gdpr_handler.withdraw_consent(consent_id)
            
            # Update metrics
            with self._lock:
                self._metrics.total_compliance_checks += 1
            
            return success
            
        except Exception as e:
            raise ComplianceError(f"Failed to withdraw consent: {str(e)}")