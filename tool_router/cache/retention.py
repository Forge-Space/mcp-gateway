"""
Cache Retention Module

This module provides comprehensive data retention and lifecycle management for the MCP Gateway caching system:
- Retention policy management
- Automatic data expiration
- Lifecycle management
- Cleanup scheduling
- Retention compliance

Key Components:
- RetentionPolicyManager: Main retention management interface
- RetentionPolicy: Define retention rules
- LifecycleManager: Manage data lifecycle
- RetentionScheduler: Schedule cleanup operations
- RetentionAuditor: Audit retention compliance
"""

import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any

from .config import CacheConfig
from .types import CacheEntryMetadata, DataClassification, RetentionError, SecurityMetrics


class RetentionAction(Enum):
    """Retention action types."""

    DELETE = "delete"
    ARCHIVE = "archive"
    ANONYMIZE = "anonymize"
    RETAIN = "retain"


class RetentionTrigger(Enum):
    """Retention trigger types."""

    TIME_BASED = "time_based"
    ACCESS_BASED = "access_based"
    SIZE_BASED = "size_based"
    MANUAL = "manual"


@dataclass
class RetentionRule:
    """Retention rule definition."""

    rule_id: str
    name: str
    description: str
    data_classification: DataClassification
    trigger: RetentionTrigger
    action: RetentionAction
    retention_days: int
    conditions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 100
    created: datetime = field(default_factory=datetime.utcnow)
    last_modified: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RetentionResult:
    """Retention operation result."""

    rule_id: str
    action: RetentionAction
    items_processed: int
    items_deleted: int
    items_archived: int
    items_anonymized: int
    errors: list[str]
    duration_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LifecycleStage:
    """Data lifecycle stage."""

    stage_id: str
    name: str
    description: str
    duration_days: int
    next_stage: str | None = None
    action: RetentionAction | None = None
    conditions: dict[str, Any] = field(default_factory=dict)


class RetentionPolicyManager:
    """Manage retention policies and rules."""

    def __init__(self, config: CacheConfig):
        """Initialize retention policy manager."""
        self.config = config
        self._lock = Lock()
        self._rules: dict[str, RetentionRule] = {}
        self._lifecycle_stages: dict[str, LifecycleStage] = {}
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

        # Initialize default retention rules
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default retention rules based on configuration."""
        default_rules = [
            RetentionRule(
                rule_id="default_sensitive",
                name="Default Sensitive Data Retention",
                description="Default retention for sensitive data",
                data_classification=DataClassification.SENSITIVE,
                trigger=RetentionTrigger.TIME_BASED,
                action=RetentionAction.DELETE,
                retention_days=self.config.retention_days.get(DataClassification.SENSITIVE, 90),
                priority=100,
            ),
            RetentionRule(
                rule_id="default_confidential",
                name="Default Confidential Data Retention",
                description="Default retention for confidential data",
                data_classification=DataClassification.CONFIDENTIAL,
                trigger=RetentionTrigger.TIME_BASED,
                action=RetentionAction.DELETE,
                retention_days=self.config.retention_days.get(DataClassification.CONFIDENTIAL, 30),
                priority=90,
            ),
            RetentionRule(
                rule_id="default_public",
                name="Default Public Data Retention",
                description="Default retention for public data",
                data_classification=DataClassification.PUBLIC,
                trigger=RetentionTrigger.TIME_BASED,
                action=RetentionAction.DELETE,
                retention_days=self.config.retention_days.get(DataClassification.PUBLIC, 365),
                priority=80,
            ),
            RetentionRule(
                rule_id="default_internal",
                name="Default Internal Data Retention",
                description="Default retention for internal data",
                data_classification=DataClassification.INTERNAL,
                trigger=RetentionTrigger.TIME_BASED,
                action=RetentionAction.DELETE,
                retention_days=self.config.retention_days.get(DataClassification.INTERNAL, 180),
                priority=85,
            ),
        ]

        for rule in default_rules:
            self._rules[rule.rule_id] = rule

    def add_rule(self, rule: RetentionRule) -> str:
        """Add a new retention rule."""
        with self._lock:
            self._rules[rule.rule_id] = rule
            rule.last_modified = datetime.utcnow()

        return rule.rule_id

    def update_rule(self, rule_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing retention rule."""
        with self._lock:
            if rule_id not in self._rules:
                return False

            rule = self._rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)

            rule.last_modified = datetime.utcnow()
            return True

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a retention rule."""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                return True
            return False

    def get_rules(self, classification: DataClassification | None = None) -> list[RetentionRule]:
        """Get retention rules, optionally filtered by classification."""
        with self._lock:
            rules = list(self._rules.values())
            if classification:
                rules = [r for r in rules if r.data_classification == classification]
            return sorted(rules, key=lambda r: r.priority, reverse=True)

    def evaluate_retention(self, metadata: CacheEntryMetadata) -> RetentionRule | None:
        """Evaluate which retention rule applies to cache entry."""
        applicable_rules = []

        with self._lock:
            rules = self.get_rules(metadata.data_classification)

            for rule in rules:
                if not rule.enabled:
                    continue

                # Check if rule conditions are met
                if self._evaluate_conditions(rule, metadata):
                    applicable_rules.append(rule)

        # Return highest priority rule
        return applicable_rules[0] if applicable_rules else None

    def _evaluate_conditions(self, rule: RetentionRule, metadata: CacheEntryMetadata) -> bool:
        """Evaluate rule conditions against metadata."""
        conditions = rule.conditions

        # Time-based condition
        if rule.trigger == RetentionTrigger.TIME_BASED:
            created_age = (datetime.utcnow() - metadata.created).days
            return created_age >= rule.retention_days

        # Access-based condition
        if rule.trigger == RetentionTrigger.ACCESS_BASED:
            if metadata.last_accessed:
                access_age = (datetime.utcnow() - metadata.last_accessed).days
                return access_age >= rule.retention_days
            # No access record, use creation time
            created_age = (datetime.utcnow() - metadata.created).days
            return created_age >= rule.retention_days

        # Size-based condition
        if rule.trigger == RetentionTrigger.SIZE_BASED:
            # This would require cache size information
            # For now, default to time-based
            created_age = (datetime.utcnow() - metadata.created).days
            return created_age >= rule.retention_days

        return False

    def apply_retention_action(
        self, key: str, metadata: CacheEntryMetadata, cache_delete_func: Callable[[str], bool]
    ) -> RetentionResult:
        """Apply retention action to a cache entry."""
        rule = self.evaluate_retention(metadata)
        if not rule:
            raise RetentionError(f"No applicable retention rule found for key: {key}")

        start_time = time.time()
        items_processed = 1
        items_deleted = 0
        items_archived = 0
        items_anonymized = 0
        errors = []

        try:
            if rule.action == RetentionAction.DELETE:
                success = cache_delete_func(key)
                if success:
                    items_deleted = 1
                else:
                    errors.append(f"Failed to delete cache entry: {key}")

            elif rule.action == RetentionAction.ARCHIVE:
                # Archive logic would go here
                items_archived = 1

            elif rule.action == RetentionAction.ANONYMIZE:
                # Anonymization logic would go here
                items_anonymized = 1

            # Update metrics
            with self._lock:
                self._metrics.audit_entries += 1

        except Exception as e:
            errors.append(f"Error applying retention action: {e!s}")

        duration = time.time() - start_time

        return RetentionResult(
            rule_id=rule.rule_id,
            action=rule.action,
            items_processed=items_processed,
            items_deleted=items_deleted,
            items_archived=items_archived,
            items_anonymized=items_anonymized,
            errors=errors,
            duration_seconds=duration,
        )


class LifecycleManager:
    """Manage data lifecycle stages."""

    def __init__(self, config: CacheConfig):
        """Initialize lifecycle manager."""
        self.config = config
        self._lock = Lock()
        self._stages: dict[str, LifecycleStage] = {}

        # Initialize default lifecycle stages
        self._initialize_default_stages()

    def _initialize_default_stages(self) -> None:
        """Initialize default lifecycle stages."""
        default_stages = [
            LifecycleStage(
                stage_id="active",
                name="Active",
                description="Data is actively used and frequently accessed",
                duration_days=30,
                next_stage="warm",
            ),
            LifecycleStage(
                stage_id="warm",
                name="Warm",
                description="Data is accessed occasionally",
                duration_days=60,
                next_stage="cold",
            ),
            LifecycleStage(
                stage_id="cold",
                name="Cold",
                description="Data is rarely accessed",
                duration_days=90,
                next_stage="archive",
            ),
            LifecycleStage(
                stage_id="archive",
                name="Archive",
                description="Data is archived for long-term storage",
                duration_days=365,
                next_stage="purge",
            ),
            LifecycleStage(
                stage_id="purge",
                name="Purge",
                description="Data is scheduled for deletion",
                duration_days=30,
                action=RetentionAction.DELETE,
            ),
        ]

        for stage in default_stages:
            self._stages[stage.stage_id] = stage

    def add_stage(self, stage: LifecycleStage) -> str:
        """Add a new lifecycle stage."""
        with self._lock:
            self._stages[stage.stage_id] = stage

        return stage.stage_id

    def get_current_stage(self, metadata: CacheEntryMetadata) -> LifecycleStage | None:
        """Determine current lifecycle stage for cache entry."""
        age_days = (datetime.utcnow() - metadata.created).days

        with self._lock:
            stages = sorted(self._stages.values(), key=lambda s: s.duration_days)

            current_stage = None
            cumulative_days = 0

            for stage in stages:
                cumulative_days += stage.duration_days
                if age_days <= cumulative_days:
                    current_stage = stage
                    break

            return current_stage

    def get_next_stage(self, current_stage_id: str) -> LifecycleStage | None:
        """Get the next stage in the lifecycle."""
        with self._lock:
            if current_stage_id in self._stages:
                current_stage = self._stages[current_stage_id]
                if current_stage.next_stage and current_stage.next_stage in self._stages:
                    return self._stages[current_stage.next_stage]
            return None

    def should_transition(self, metadata: CacheEntryMetadata) -> bool:
        """Check if data should transition to next lifecycle stage."""
        current_stage = self.get_current_stage(metadata)
        if not current_stage:
            return False

        # Check if current stage duration has passed
        age_days = (datetime.utcnow() - metadata.created).days

        # This is a simplified check - in practice, you'd track when each stage started
        return age_days > current_stage.duration_days


class RetentionScheduler:
    """Schedule and execute retention operations."""

    def __init__(self, retention_manager: RetentionPolicyManager, config: CacheConfig):
        """Initialize retention scheduler."""
        self.retention_manager = retention_manager
        self.config = config
        self._lock = Lock()
        self._running = False
        self._scheduler_thread: threading.Thread | None = None
        self._cleanup_interval = getattr(config, "retention_cleanup_interval_hours", 24) * 3600  # Convert to seconds

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Start the retention scheduler."""
        with self._lock:
            if self._running:
                return

            self._running = True
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()

            self.logger.info("Retention scheduler started")

    def stop(self) -> None:
        """Stop the retention scheduler."""
        with self._lock:
            if not self._running:
                return

            self._running = False
            if self._scheduler_thread:
                self._scheduler_thread.join(timeout=10)

            self.logger.info("Retention scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                self._perform_cleanup()
                time.sleep(self._cleanup_interval)
            except Exception as e:
                self.logger.error(f"Error in retention scheduler: {e!s}")
                time.sleep(60)  # Wait before retrying

    def _perform_cleanup(self) -> None:
        """Perform retention cleanup."""
        # This would integrate with the actual cache to perform cleanup
        # For now, we'll just log the cleanup operation
        self.logger.info("Performing retention cleanup")

        # In a real implementation, this would:
        # 1. Scan cache entries
        # 2. Apply retention rules
        # 3. Execute retention actions
        # 4. Update metrics

    def trigger_cleanup_now(self) -> None:
        """Trigger an immediate cleanup operation."""
        threading.Thread(target=self._perform_cleanup, daemon=True).start()


class RetentionAuditor:
    """Audit retention compliance."""

    def __init__(self, retention_manager: RetentionPolicyManager, config: CacheConfig):
        """Initialize retention auditor."""
        self.retention_manager = retention_manager
        self.config = config
        self._lock = Lock()

    def audit_retention_compliance(self) -> dict[str, Any]:
        """Audit retention compliance."""
        audit_results = {
            "audit_timestamp": datetime.utcnow().isoformat(),
            "total_rules": 0,
            "enabled_rules": 0,
            "disabled_rules": 0,
            "rules_by_classification": {},
            "compliance_score": 0.0,
            "findings": [],
            "recommendations": [],
        }

        rules = self.retention_manager.get_rules()
        audit_results["total_rules"] = len(rules)

        # Count enabled/disabled rules
        enabled_count = sum(1 for r in rules if r.enabled)
        audit_results["enabled_rules"] = enabled_count
        audit_results["disabled_rules"] = len(rules) - enabled_count

        # Group by classification
        classification_counts = defaultdict(int)
        for rule in rules:
            classification_counts[rule.data_classification.value] += 1

        audit_results["rules_by_classification"] = dict(classification_counts)

        # Calculate compliance score
        if len(rules) > 0:
            base_score = (enabled_count / len(rules)) * 100

            # Deduct points for missing classifications
            required_classifications = [DataClassification.SENSITIVE, DataClassification.CONFIDENTIAL]
            for classification in required_classifications:
                if classification.value not in classification_counts:
                    base_score -= 20
                    audit_results["findings"].append(f"Missing retention rule for {classification.value} data")
                    audit_results["recommendations"].append(f"Create retention rule for {classification.value} data")

            audit_results["compliance_score"] = max(0, base_score)

        return audit_results

    def get_retention_metrics(self) -> SecurityMetrics:
        """Get retention metrics."""
        return self.retention_manager.get_metrics()
