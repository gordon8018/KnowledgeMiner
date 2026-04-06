"""
Alert management for knowledge compiler monitoring.

Provides configurable alert rules, threshold management,
and alert delivery with deduplication and cooldown.
"""

import time
import smtplib
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging


logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    description: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    duration_seconds: int = 60  # How long condition must persist
    cooldown_seconds: int = 300  # Minimum time between alerts
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert instance."""
    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    metric_value: float
    threshold: float
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertNotification:
    """Alert notification configuration."""
    name: str
    type: str  # "email", "webhook", "log"
    config: Dict[str, Any]
    min_severity: AlertSeverity = AlertSeverity.WARNING


class AlertManager:
    """
    Manages alert rules and notifications.

    Features:
    - Configurable alert rules with thresholds
    - Alert deduplication and cooldown
    - Multiple notification channels (email, webhook, log)
    - Alert acknowledgment and resolution tracking
    - Alert history and statistics
    """

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.notifications: Dict[str, AlertNotification] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.condition_start_times: Dict[str, datetime] = {}
        self.alert_count = 0
        self._lock = __import__("threading").Lock()

    def add_rule(self, rule: AlertRule):
        """Add alert rule."""
        with self._lock:
            self.rules[rule.name] = rule
            logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove alert rule."""
        with self._lock:
            if rule_name in self.rules:
                del self.rules[rule_name]
                logger.info(f"Removed alert rule: {rule_name}")

    def add_notification(self, notification: AlertNotification):
        """Add notification channel."""
        with self._lock:
            self.notifications[notification.name] = notification
            logger.info(f"Added notification channel: {notification.name}")

    def evaluate_rule(
        self,
        rule: AlertRule,
        metric_value: float,
        current_time: Optional[datetime] = None
    ) -> Optional[Alert]:
        """
        Evaluate alert rule against metric value.

        Args:
            rule: Alert rule to evaluate
            metric_value: Current metric value
            current_time: Current time (default: now)

        Returns:
            Alert if condition triggered, None otherwise
        """
        if not rule.enabled:
            return None

        current_time = current_time or datetime.utcnow()

        # Check if condition is met
        condition_met = self._check_condition(
            metric_value,
            rule.threshold,
            rule.condition
        )

        rule_key = f"{rule.name}:{tuple(sorted(rule.labels.items()))}"

        if condition_met:
            # Track when condition started
            if rule_key not in self.condition_start_times:
                self.condition_start_times[rule_key] = current_time

            # Check if condition persisted long enough
            condition_duration = (
                current_time - self.condition_start_times[rule_key]
            ).total_seconds()

            if condition_duration >= rule.duration_seconds:
                # Check cooldown
                if rule_key in self.alert_cooldowns:
                    cooldown_expiry = self.alert_cooldowns[rule_key] + timedelta(
                        seconds=rule.cooldown_seconds
                    )
                    if current_time < cooldown_expiry:
                        return None  # Still in cooldown

                # Create alert
                alert = self._create_alert(rule, metric_value, current_time)
                self.alert_cooldowns[rule_key] = current_time
                return alert
        else:
            # Condition not met, reset start time
            if rule_key in self.condition_start_times:
                del self.condition_start_times[rule_key]

        return None

    def _check_condition(
        self,
        value: float,
        threshold: float,
        condition: str
    ) -> bool:
        """Check if condition is met."""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return value == threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    def _create_alert(
        self,
        rule: AlertRule,
        metric_value: float,
        current_time: datetime
    ) -> Alert:
        """Create alert from rule."""
        self.alert_count += 1
        alert_id = f"alert_{self.alert_count}_{int(current_time.timestamp())}"

        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=self._generate_alert_message(rule, metric_value),
            metric_value=metric_value,
            threshold=rule.threshold,
            triggered_at=current_time,
            labels=rule.labels.copy()
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        logger.warning(f"Alert triggered: {alert_id} - {alert.message}")

        return alert

    def _generate_alert_message(self, rule: AlertRule, metric_value: float) -> str:
        """Generate alert message."""
        condition_text = {
            "gt": "greater than",
            "lt": "less than",
            "eq": "equal to",
            "gte": "greater than or equal to",
            "lte": "less than or equal to"
        }.get(rule.condition, rule.condition)

        return (
            f"{rule.description}: {rule.metric_name} is {condition_text} "
            f"{rule.threshold} (current value: {metric_value})"
        )

    def send_alert(self, alert: Alert):
        """Send alert through all notification channels."""
        for notification in self.notifications.values():
            if self._should_send_notification(alert, notification):
                try:
                    self._send_notification(alert, notification)
                except Exception as e:
                    logger.error(
                        f"Failed to send notification via {notification.name}: {e}"
                    )

    def _should_send_notification(
        self,
        alert: Alert,
        notification: AlertNotification
    ) -> bool:
        """Check if alert should be sent via notification channel."""
        severity_order = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.ERROR: 2,
            AlertSeverity.CRITICAL: 3
        }

        return severity_order[alert.severity] >= severity_order[notification.min_severity]

    def _send_notification(self, alert: Alert, notification: AlertNotification):
        """Send notification via specific channel."""
        if notification.type == "email":
            self._send_email_notification(alert, notification.config)
        elif notification.type == "webhook":
            self._send_webhook_notification(alert, notification.config)
        elif notification.type == "log":
            self._send_log_notification(alert)
        else:
            logger.warning(f"Unknown notification type: {notification.type}")

    def _send_email_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg["From"] = config["from"]
            msg["To"] = config["to"]
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.rule_name}"

            body = f"""
Alert: {alert.message}

Severity: {alert.severity.value}
Rule: {alert.rule_name}
Metric Value: {alert.metric_value}
Threshold: {alert.threshold}
Triggered At: {alert.triggered_at}

Alert ID: {alert.id}
            """

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(
                config.get("smtp_host", "localhost"),
                config.get("smtp_port", 587)
            ) as server:
                if config.get("smtp_use_tls", True):
                    server.starttls()
                if "smtp_username" in config:
                    server.login(
                        config["smtp_username"],
                        config["smtp_password"]
                    )
                server.send_message(msg)

            logger.info(f"Sent email notification for alert {alert.id}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def _send_webhook_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send webhook notification."""
        try:
            import requests

            webhook_url = config["url"]
            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "message": alert.message,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
                "triggered_at": alert.triggered_at.isoformat(),
                "labels": alert.labels
            }

            headers = config.get("headers", {})
            timeout = config.get("timeout", 10)

            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()

            logger.info(f"Sent webhook notification for alert {alert.id}")

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            raise

    def _send_log_notification(self, alert: Alert):
        """Send log notification."""
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(alert.severity, logger.warning)

        log_func(f"ALERT: {alert.message} (Alert ID: {alert.id})")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge alert."""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.metadata["acknowledged_by"] = acknowledged_by
                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")

    def resolve_alert(self, alert_id: str):
        """Resolve alert."""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                del self.active_alerts[alert_id]
                logger.info(f"Alert {alert_id} resolved")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())

    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get alert history."""
        history = self.alert_history[-limit:]

        if severity:
            history = [a for a in history if a.severity == severity]

        return history

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        total = len(self.alert_history)
        by_severity = {
            severity.value: sum(
                1 for a in self.alert_history
                if a.severity == severity
            )
            for severity in AlertSeverity
        }

        active_by_severity = {
            severity.value: sum(
                1 for a in self.active_alerts.values()
                if a.severity == severity
            )
            for severity in AlertSeverity
        }

        return {
            "total_alerts": total,
            "active_alerts": len(self.active_alerts),
            "by_severity": by_severity,
            "active_by_severity": active_by_severity
        }
