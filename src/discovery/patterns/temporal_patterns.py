"""
Temporal pattern detection utilities.
"""

from typing import List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re


def extract_time_references(text: str) -> List[datetime]:
    """
    Extract time references from text.

    Args:
        text: Text to search for time references

    Returns:
        List of datetime objects found
    """
    time_references = []

    # ISO date format: YYYY-MM-DD
    iso_pattern = r'\d{4}-\d{2}-\d{2}'
    for match in re.finditer(iso_pattern, text):
        try:
            date = datetime.fromisoformat(match.group())
            time_references.append(date)
        except ValueError:
            continue

    # Chinese date format: YYYY年MM月DD日
    chinese_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    for match in re.finditer(chinese_pattern, text):
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            date = datetime(year, month, day)
            time_references.append(date)
        except ValueError:
            continue

    return time_references


def detect_periodicity(time_references: List[datetime], tolerance_days: int = 7) -> List[str]:
    """
    Detect periodic patterns in time references.

    Args:
        time_references: List of datetime objects
        tolerance_days: Tolerance for period detection (in days)

    Returns:
        List of period descriptions (e.g., "weekly", "monthly")
    """
    if len(time_references) < 3:
        return []  # Need at least 3 data points

    # Sort time references
    sorted_times = sorted(time_references)

    # Compute intervals between consecutive times
    intervals = []
    for i in range(1, len(sorted_times)):
        interval = (sorted_times[i] - sorted_times[i-1]).days
        intervals.append(interval)

    # Detect patterns based on interval consistency
    periods = []

    if not intervals:
        return periods

    avg_interval = sum(intervals) / len(intervals)

    # Check for weekly pattern (around 7 days)
    if abs(avg_interval - 7) <= tolerance_days:
        periods.append("weekly")

    # Check for monthly pattern (around 30 days)
    if abs(avg_interval - 30) <= tolerance_days * 4:
        periods.append("monthly")

    # Check for quarterly pattern (around 90 days)
    if abs(avg_interval - 90) <= tolerance_days * 10:
        periods.append("quarterly")

    # Check for yearly pattern (around 365 days)
    if abs(avg_interval - 365) <= tolerance_days * 30:
        periods.append("yearly")

    return periods


def bin_time_references(time_references: List[datetime], bin_size_days: int = 30) -> List[Tuple[datetime, datetime, int]]:
    """
    Bin time references into time windows.

    Args:
        time_references: List of datetime objects
        bin_size_days: Size of each time bin in days

    Returns:
        List of (start_time, end_time, count) tuples
    """
    if not time_references:
        return []

    # Find time range
    min_time = min(time_references)
    max_time = max(time_references)

    # Create bins
    bins = []
    current_start = min_time

    while current_start < max_time:
        current_end = current_start + timedelta(days=bin_size_days)

        # Count references in this bin
        count = sum(
            1 for t in time_references
            if current_start <= t < current_end
        )

        if count > 0:
            bins.append((current_start, current_end, count))

        current_start = current_end

    return bins
