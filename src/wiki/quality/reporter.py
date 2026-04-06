"""
QualityReporter for generating quality reports and tracking trends.

This module provides comprehensive reporting capabilities for Wiki quality monitoring,
including trend analysis, dashboard data preparation, and alert systems.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
import logging

from src.wiki.core.storage import WikiStore
from src.wiki.quality.models import (
    Issue,
    IssueType,
    IssueSeverity,
    QualityReport,
    HealthCheckResult,
    TrendDirection,
    MetricType,
    ExtendedQualityReport,
    TrendPoint,
    TrendAnalysis,
    DashboardData
)


logger = logging.getLogger(__name__)


class QualityReporter:
    """
    Generates quality reports and tracks quality trends over time.

    This class provides comprehensive reporting capabilities including:
    - Markdown and JSON report generation
    - Trend analysis with predictions
    - Dashboard data preparation
    - Alert system for quality degradation
    """

    def __init__(self, wiki_store: WikiStore, output_dir: str):
        """
        Initialize the QualityReporter.

        Args:
            wiki_store: WikiStore instance for accessing Wiki data
            output_dir: Directory to save generated reports
        """
        self.wiki_store = wiki_store
        self.output_dir = output_dir
        self.report_history: List[ExtendedQualityReport] = []

        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Load existing report history
        self._load_report_history()

        logger.info(f"QualityReporter initialized with output directory: {output_dir}")

    def _load_report_history(self):
        """Load existing reports from output directory."""
        try:
            for file_path in Path(self.output_dir).glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        report = ExtendedQualityReport(**data)
                        self.report_history.append(report)
                except Exception as e:
                    logger.warning(f"Failed to load report from {file_path}: {e}")

            # Sort by generated_at
            self.report_history.sort(key=lambda r: r.generated_at)
            logger.info(f"Loaded {len(self.report_history)} historical reports")

        except Exception as e:
            logger.warning(f"Failed to load report history: {e}")

    def generate_report(self, health_check_result: HealthCheckResult) -> ExtendedQualityReport:
        """
        Generate comprehensive quality report from health check result.

        Args:
            health_check_result: Result from health check

        Returns:
            ExtendedQualityReport with all findings
        """
        timestamp = datetime.now()
        report_id = f"qr-{timestamp.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Calculate time range (last 7 days by default)
        time_range_end = timestamp
        time_range_start = timestamp - timedelta(days=7)

        # Determine quality trend
        quality_trend = self._determine_trend(health_check_result.quality_report.overall_score)

        # Create issue breakdown
        issue_breakdown = self._create_issue_breakdown(
            health_check_result.consistency_issues +
            health_check_result.staleness_issues
        )

        # Generate detailed findings
        detailed_findings = self._generate_detailed_findings(health_check_result)

        # Generate recommendations
        recommendations = self._generate_recommendations(health_check_result)

        # Create report
        report = ExtendedQualityReport(
            report_id=report_id,
            generated_at=timestamp,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            overall_score=health_check_result.quality_report.overall_score,
            total_pages=health_check_result.quality_report.page_count,
            total_issues=health_check_result.total_issues,
            critical_issues=health_check_result.critical_issues,
            quality_trend=quality_trend,
            issue_breakdown=issue_breakdown,
            recommendations=recommendations,
            detailed_findings=detailed_findings,
            report_file_path=""  # Will be set after saving
        )

        # Save report files
        report_base_path = os.path.join(self.output_dir, f"{timestamp.strftime('%Y%m%d_%H%M%S')}_quality_report")
        markdown_path = f"{report_base_path}.md"
        json_path = f"{report_base_path}.json"

        # Save markdown report
        self._save_markdown_report(report, health_check_result, markdown_path)

        # Save JSON report
        self._save_json_report(report, json_path)

        # Update report with file path
        report.report_file_path = markdown_path

        # Add to history
        self.report_history.append(report)

        logger.info(f"Generated quality report: {report_id}")
        return report

    def _determine_trend(self, current_score: float) -> TrendDirection:
        """Determine quality trend based on historical data."""
        if len(self.report_history) < 2:
            return TrendDirection.UNKNOWN

        # Compare with previous report
        previous_score = self.report_history[-1].overall_score
        change = current_score - previous_score
        change_percentage = (change / previous_score) * 100 if previous_score > 0 else 0

        if change_percentage > 5:
            return TrendDirection.IMPROVING
        elif change_percentage < -5:
            return TrendDirection.DEGRADING
        else:
            return TrendDirection.STABLE

    def _create_issue_breakdown(self, issues: List[Issue]) -> Dict[str, int]:
        """Create breakdown of issues by type."""
        breakdown = {}
        for issue in issues:
            # issue_type is already a string due to use_enum_values=True
            issue_type = issue.issue_type if isinstance(issue.issue_type, str) else issue.issue_type.value
            breakdown[issue_type] = breakdown.get(issue_type, 0) + 1
        return breakdown

    def _generate_detailed_findings(self, health_check_result: HealthCheckResult) -> List[str]:
        """Generate detailed findings from health check result."""
        findings = []

        # Overall assessment
        score = health_check_result.quality_report.overall_score
        if score >= 0.9:
            findings.append("Wiki quality is excellent with minimal issues detected.")
        elif score >= 0.75:
            findings.append("Wiki quality is good with some areas for improvement.")
        elif score >= 0.6:
            findings.append("Wiki quality is fair with several issues requiring attention.")
        else:
            findings.append("Wiki quality is poor and requires immediate attention.")

        # Consistency findings
        if health_check_result.consistency_issues:
            findings.append(
                f"Detected {len(health_check_result.consistency_issues)} consistency issues "
                f"including orphan pages, broken links, and circular references."
            )

        # Staleness findings
        if health_check_result.staleness_issues:
            findings.append(
                f"Detected {len(health_check_result.staleness_issues)} pages with stale content "
                f"that may require updates."
            )

        # Dimension-specific findings
        qr = health_check_result.quality_report
        if qr.completeness_score < 0.7:
            findings.append("Content completeness is below threshold; many pages may be incomplete.")
        if qr.freshness_score < 0.7:
            findings.append("Content freshness is declining; consider updating older pages.")
        if qr.metadata_score < 0.7:
            findings.append("Metadata quality is insufficient; improve tagging and categorization.")

        return findings

    def _generate_recommendations(self, health_check_result: HealthCheckResult) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Start with existing recommendations
        recommendations.extend(health_check_result.quality_report.recommendations)

        # Add specific recommendations based on issues
        critical_count = health_check_result.critical_issues
        if critical_count > 10:
            recommendations.append(
                f"URGENT: {critical_count} critical issues detected - immediate action required"
            )

        # Quality score recommendations
        score = health_check_result.quality_report.overall_score
        if score < 0.6:
            recommendations.append("Implement daily quality monitoring to track improvements")
            recommendations.append("Consider automated content validation checks")

        # Specific issue recommendations
        issue_types = set(i.issue_type for i in health_check_result.consistency_issues)
        if "orphan_page" in issue_types:
            recommendations.append("Review and link orphan pages to improve navigation")
        if "broken_link" in issue_types:
            recommendations.append("Fix broken links to maintain data integrity")
        if "stale_content" in issue_types:
            recommendations.append("Update stale content to maintain relevance")

        return recommendations

    def _save_markdown_report(self, report: ExtendedQualityReport, health_check_result: HealthCheckResult, file_path: str):
        """Save report as markdown file."""
        content = self._generate_markdown_content(report, health_check_result)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.debug(f"Saved markdown report to {file_path}")

    def _generate_markdown_content(self, report: ExtendedQualityReport, health_check_result: HealthCheckResult) -> str:
        """Generate markdown content for report."""
        qr = health_check_result.quality_report

        # Determine status and emoji
        if report.overall_score >= 0.9:
            status = "Excellent"
            emoji = "✅"
        elif report.overall_score >= 0.75:
            status = "Good"
            emoji = "👍"
        elif report.overall_score >= 0.6:
            status = "Fair"
            emoji = "⚠️"
        else:
            status = "Poor"
            emoji = "🔴"

        # Trend emoji
        trend_emoji = {
            TrendDirection.IMPROVING: "📈",
            TrendDirection.STABLE: "➡️",
            TrendDirection.DEGRADING: "📉",
            TrendDirection.UNKNOWN: "❓"
        }.get(report.quality_trend, "❓")

        content = f"""# Wiki Quality Report
**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Time Range:** {report.time_range_start.strftime('%Y-%m-%d')} to {report.time_range_end.strftime('%Y-%m-%d')}

## Executive Summary
- **Overall Quality Score:** {report.overall_score:.2f}/1.0
- **Total Pages:** {report.total_pages}
- **Total Issues:** {report.total_issues}
- **Critical Issues:** {report.critical_issues}
- **Quality Trend:** {report.quality_trend.value.title()} {trend_emoji}

## Quality Scores

### Overall Quality
**Score:** {report.overall_score:.2f}/1.0
**Status:** {status} {emoji}

### Dimension Scores
- **Completeness:** {qr.completeness_score:.2f}/1.0 - {self._describe_score(qr.completeness_score)}
- **Freshness:** {qr.freshness_score:.2f}/1.0 - {self._describe_score(qr.freshness_score)}
- **Metadata:** {qr.metadata_score:.2f}/1.0 - {self._describe_score(qr.metadata_score)}

## Issue Breakdown

### By Type
"""

        # Issue breakdown table
        if report.issue_breakdown:
            content += "| Type | Count |\n"
            content += "|------|-------|\n"
            for issue_type, count in sorted(report.issue_breakdown.items()):
                content += f"| {issue_type.replace('_', ' ').title()} | {count} |\n"
        else:
            content += "No issues detected. 🎉\n"

        # Severity breakdown
        content += "\n### By Severity\n"
        content += "| Severity | Count |\n"
        content += "|----------|-------|\n"

        severity_counts = self._count_by_severity(
            health_check_result.consistency_issues +
            health_check_result.staleness_issues
        )
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            content += f"| {severity.title()} | {count} |\n"

        # Critical issues
        critical_issues = [
            i for i in (health_check_result.consistency_issues + health_check_result.staleness_issues)
            if i.severity == "critical"  # Already a string due to use_enum_values=True
        ]

        content += "\n## Critical Issues Requiring Attention\n"
        if critical_issues:
            for i, issue in enumerate(critical_issues[:10], 1):
                issue_type_str = issue.issue_type.replace('_', ' ').title() if isinstance(issue.issue_type, str) else issue.issue_type.value.replace('_', ' ').title()
                content += f"{i}. **{issue_type_str}** - {issue.description}\n"
                content += f"   - Page: {issue.page_id}\n"
                content += f"   - Detected: {issue.detected_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        else:
            content += "No critical issues detected. ✅\n"

        # Recommendations
        content += "\n## Recommendations\n"
        for i, rec in enumerate(report.recommendations, 1):
            content += f"{i}. {rec}\n"

        # Detailed findings
        content += "\n## Detailed Findings\n"
        for finding in report.detailed_findings:
            content += f"- {finding}\n"

        # Footer
        content += f"""
---
**Report ID:** {report.report_id}
**Generated by:** KnowledgeMiner 3.0 Quality System
"""

        return content

    def _describe_score(self, score: float) -> str:
        """Describe a quality score."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.75:
            return "Good"
        elif score >= 0.6:
            return "Fair"
        else:
            return "Poor"

    def _count_by_severity(self, issues: List[Issue]) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {}
        for issue in issues:
            # severity is already a string due to use_enum_values=True
            severity = issue.severity if isinstance(issue.severity, str) else issue.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _save_json_report(self, report: ExtendedQualityReport, file_path: str):
        """Save report as JSON file."""
        data = report.model_dump(mode='json')

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        logger.debug(f"Saved JSON report to {file_path}")

    def track_trend(self, report_history: List[ExtendedQualityReport]) -> TrendAnalysis:
        """
        Analyze quality trends over time.

        Args:
            report_history: List of historical quality reports

        Returns:
            TrendAnalysis with direction, confidence, and predictions
        """
        if len(report_history) < 3:
            return TrendAnalysis(
                direction=TrendDirection.UNKNOWN,
                confidence=0.0,
                trend_points=[],
                summary="Insufficient data for trend analysis (need at least 3 reports)",
                recommendations=["Continue monitoring to establish trend patterns"]
            )

        # Sort reports by date
        sorted_reports = sorted(report_history, key=lambda r: r.generated_at)

        # Calculate trend points
        trend_points = []
        for i, report in enumerate(sorted_reports):
            if i == 0:
                change_from_previous = 0.0
                change_percentage = 0.0
            else:
                prev_score = sorted_reports[i-1].overall_score
                change_from_previous = report.overall_score - prev_score
                change_percentage = (change_from_previous / prev_score * 100) if prev_score > 0 else 0.0

            point = TrendPoint(
                timestamp=report.generated_at,
                metric_type=MetricType.OVERALL_QUALITY,
                value=report.overall_score,
                change_from_previous=change_from_previous,
                change_percentage=change_percentage
            )
            trend_points.append(point)

        # Calculate moving averages
        scores = [r.overall_score for r in sorted_reports]
        ma_3 = mean(scores[-3:]) if len(scores) >= 3 else scores[-1]
        ma_7 = mean(scores[-7:]) if len(scores) >= 7 else ma_3

        # Determine trend direction
        recent_avg = mean(scores[-3:])
        older_avg = mean(scores[:-3]) if len(scores) > 3 else mean(scores[:3])

        overall_change = recent_avg - older_avg
        overall_change_pct = (overall_change / older_avg * 100) if older_avg > 0 else 0

        if overall_change_pct > 5:
            direction = TrendDirection.IMPROVING
            confidence = min(0.5 + (overall_change_pct / 20), 1.0)
        elif overall_change_pct < -5:
            direction = TrendDirection.DEGRADING
            confidence = min(0.5 + (abs(overall_change_pct) / 20), 1.0)
        else:
            direction = TrendDirection.STABLE
            confidence = 0.7  # High confidence for stable

        # Generate summary
        summary = self._generate_trend_summary(direction, overall_change_pct, recent_avg)

        # Predict future quality (linear regression)
        predicted_quality = self._predict_quality(scores)

        # Generate recommendations
        recommendations = self._generate_trend_recommendations(direction, overall_change_pct)

        return TrendAnalysis(
            direction=direction,
            confidence=confidence,
            trend_points=trend_points,
            summary=summary,
            predicted_quality_30_days=predicted_quality,
            recommendations=recommendations
        )

    def _generate_trend_summary(self, direction: TrendDirection, change_pct: float, recent_avg: float) -> str:
        """Generate trend analysis summary."""
        direction_str = direction.value.title()

        if direction == TrendDirection.IMPROVING:
            return (
                f"Quality is {direction_str.lower()}: showing {change_pct:.1f}% improvement "
                f"with current score of {recent_avg:.2f}. Keep up the good work!"
            )
        elif direction == TrendDirection.DEGRADING:
            return (
                f"Quality is {direction_str.lower()}: showing {abs(change_pct):.1f}% decline "
                f"with current score of {recent_avg:.2f}. Immediate attention required."
            )
        else:
            return (
                f"Quality is {direction_str.lower()}: maintaining score of {recent_avg:.2f} "
                f"with minimal fluctuation. Continue current practices."
            )

    def _predict_quality(self, scores: List[float]) -> Optional[float]:
        """Predict quality score in 30 days using linear regression."""
        if len(scores) < 3:
            return None

        try:
            # Simple linear regression
            x = list(range(len(scores)))
            y = scores

            n = len(scores)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi ** 2 for xi in x)

            # Calculate slope and intercept
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n

            # Predict 30 days ahead (approximately 30 data points if daily)
            future_x = len(scores) + 30
            predicted = slope * future_x + intercept

            # Clamp to valid range
            return max(0.0, min(1.0, predicted))

        except Exception as e:
            logger.warning(f"Failed to predict quality: {e}")
            return None

    def _generate_trend_recommendations(self, direction: TrendDirection, change_pct: float) -> List[str]:
        """Generate recommendations based on trend."""
        if direction == TrendDirection.IMPROVING:
            return [
                "Continue current quality maintenance practices",
                "Document successful improvement strategies",
                "Consider setting higher quality targets"
            ]
        elif direction == TrendDirection.DEGRADING:
            return [
                "URGENT: Investigate root cause of quality decline",
                "Increase monitoring frequency to daily checks",
                "Implement automated quality gates",
                "Review recent content changes for issues"
            ]
        else:
            return [
                "Maintain current quality practices",
                "Look for opportunities to incrementally improve",
                "Consider setting higher quality targets"
            ]

    def create_dashboard_data(self, reports: List[ExtendedQualityReport]) -> DashboardData:
        """
        Prepare data for visualization dashboard.

        Args:
            reports: List of quality reports

        Returns:
            DashboardData with chart information
        """
        if not reports:
            return DashboardData(
                generated_at=datetime.now(),
                time_range_days=0,
                quality_over_time=[],
                issue_distribution={},
                repair_progress={},
                top_issues=[],
                charts={}
            )

        # Sort reports by date
        sorted_reports = sorted(reports, key=lambda r: r.generated_at)

        # Calculate time range
        time_range_days = (sorted_reports[-1].generated_at - sorted_reports[0].generated_at).days

        # Quality over time data
        quality_over_time = [
            {
                "timestamp": r.generated_at.isoformat(),
                "score": r.overall_score,
                "issues": r.total_issues,
                "critical_issues": r.critical_issues
            }
            for r in sorted_reports
        ]

        # Aggregate issue distribution
        issue_distribution = {}
        for report in sorted_reports:
            for issue_type, count in report.issue_breakdown.items():
                issue_distribution[issue_type] = issue_distribution.get(issue_type, 0) + count

        # Repair progress (mock data for now)
        repair_progress = {
            "total_issues": sum(r.total_issues for r in sorted_reports),
            "resolved_issues": 0,  # Would need actual repair tracking
            "in_progress": 0,
            "completion_rate": 0.0
        }

        # Top issues (from most recent report)
        recent_report = sorted_reports[-1]
        top_issues = [
            {
                "issue_type": issue_type,
                "count": count,
                "severity": "high" if count > 5 else "medium"
            }
            for issue_type, count in sorted(
                recent_report.issue_breakdown.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]

        # Chart data
        charts = {
            "quality_timeline": {
                "type": "line",
                "data": quality_over_time,
                "x_axis": "timestamp",
                "y_axis": "score"
            },
            "issue_distribution": {
                "type": "bar",
                "data": [{"type": k, "count": v} for k, v in issue_distribution.items()],
                "x_axis": "type",
                "y_axis": "count"
            },
            "severity_breakdown": {
                "type": "pie",
                "data": self._get_severity_breakdown(recent_report),
                "label_key": "severity",
                "value_key": "count"
            }
        }

        return DashboardData(
            generated_at=datetime.now(),
            time_range_days=time_range_days,
            quality_over_time=quality_over_time,
            issue_distribution=issue_distribution,
            repair_progress=repair_progress,
            top_issues=top_issues,
            charts=charts
        )

    def _get_severity_breakdown(self, report: ExtendedQualityReport) -> List[Dict[str, Any]]:
        """Get severity breakdown for dashboard."""
        # This would need actual severity data from issues
        # For now, return mock data based on critical issues
        return [
            {"severity": "critical", "count": report.critical_issues},
            {"severity": "high", "count": report.total_issues // 3},
            {"severity": "medium", "count": report.total_issues // 3},
            {"severity": "low", "count": report.total_issues // 3}
        ]

    def send_alert(self, health_check_result: HealthCheckResult, alert_path: Optional[str] = None) -> bool:
        """
        Send alert if quality degrades beyond threshold.

        Args:
            health_check_result: Result from health check
            alert_path: Optional path for alert log file

        Returns:
            True if alert was sent successfully, False otherwise
        """
        # Check alert conditions
        should_alert = self._should_send_alert(health_check_result)

        if not should_alert:
            logger.debug("No alert conditions met")
            return True  # Not an error, just no alert needed

        # Generate alert content
        alert_content = self._generate_alert_content(health_check_result)

        # Log alert
        logger.warning(f"Quality alert triggered: {alert_content}")

        # Save alert to file if path provided
        if alert_path:
            try:
                with open(alert_path, 'w', encoding='utf-8') as f:
                    f.write(alert_content)
                logger.info(f"Alert saved to {alert_path}")
            except Exception as e:
                logger.error(f"Failed to save alert to {alert_path}: {e}")
                return False

        return True

    def _should_send_alert(self, health_check_result: HealthCheckResult) -> bool:
        """Determine if alert should be sent."""
        # Alert if quality drops below threshold
        if health_check_result.quality_report.overall_score < 0.6:
            return True

        # Alert if too many critical issues
        if health_check_result.critical_issues > 10:
            return True

        # Alert if degrading significantly week-over-week
        if len(self.report_history) >= 7:
            recent_score = health_check_result.quality_report.overall_score
            old_score = self.report_history[-7].overall_score
            decline = (old_score - recent_score) / old_score * 100 if old_score > 0 else 0

            if decline > 10:
                return True

        return False

    def _generate_alert_content(self, health_check_result: HealthCheckResult) -> str:
        """Generate alert content."""
        score = health_check_result.quality_report.overall_score
        critical_issues = health_check_result.critical_issues
        total_issues = health_check_result.total_issues

        # Determine trend
        trend = self._determine_trend(score)

        # Get top critical issues
        critical_list = [
            i for i in (health_check_result.consistency_issues + health_check_result.staleness_issues)
            if i.severity == "critical"  # Already a string due to use_enum_values=True
        ][:5]

        content = f"""ALERT: Wiki Quality Degradation Detected
{'=' * 50}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Quality: {score:.2f}/1.0
Critical Issues: {critical_issues}
Total Issues: {total_issues}
Trend: {trend.value.upper()}

Top Critical Issues:
"""

        for i, issue in enumerate(critical_list, 1):
            issue_type_str = issue.issue_type.replace('_', ' ').title() if isinstance(issue.issue_type, str) else issue.issue_type.value.replace('_', ' ').title()
            content += f"{i}. {issue_type_str}\n"
            content += f"   Page: {issue.page_id}\n"
            content += f"   Description: {issue.description}\n\n"

        content += f"{'=' * 50}\n"
        content += "Immediate action required. Please review and address critical issues.\n"

        return content
