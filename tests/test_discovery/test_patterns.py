import pytest
from datetime import datetime
from src.discovery.patterns.relation_patterns import RelationPatternLoader, EXPLICIT_PATTERNS
from src.discovery.patterns.temporal_patterns import (
    extract_time_references,
    detect_periodicity,
    bin_time_references
)
from src.core.relation_model import RelationType


def test_relation_pattern_loader_init():
    """Test RelationPatternLoader initialization."""
    loader = RelationPatternLoader()

    assert loader.get_pattern_count() > 0
    assert len(loader._compiled_patterns) == loader.get_pattern_count()


def test_extract_explicit_relations_chinese():
    """Test extracting Chinese explicit relations."""
    loader = RelationPatternLoader()

    text = "利率上升导致股市下跌"
    relations = loader.extract_relations(text)

    assert len(relations) > 0
    source, target, rel_type = relations[0]
    assert "利率" in source
    assert "股市" in target
    assert rel_type == RelationType.CAUSES


def test_extract_explicit_relations_english():
    """Test extracting English explicit relations."""
    loader = RelationPatternLoader()

    text = "Inflation causes price increase"
    relations = loader.extract_relations(text)

    assert len(relations) > 0
    source, target, rel_type = relations[0]
    assert "inflation" in source.lower()
    assert "price" in target.lower()


def test_custom_patterns():
    """Test custom pattern overriding."""
    custom_patterns = {
        r'CUSTOM\s+(\S+)\s+(\S+)': RelationType.RELATED_TO
    }
    loader = RelationPatternLoader(custom_patterns=custom_patterns)

    assert loader.get_pattern_count() >= len(EXPLICIT_PATTERNS)


def test_extract_time_references_iso():
    """Test extracting ISO format time references."""
    text = "文档创建于2024-03-15，更新于2024-04-20"
    times = extract_time_references(text)

    assert len(times) == 2
    assert times[0] == datetime(2024, 3, 15)


def test_extract_time_references_chinese():
    """Test extracting Chinese format time references."""
    text = "会议在2024年5月10日举行"
    times = extract_time_references(text)

    assert len(times) == 1
    assert times[0] == datetime(2024, 5, 10)


def test_detect_periodicity_weekly():
    """Test detecting weekly periodicity."""
    times = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 8),
        datetime(2024, 1, 15),
        datetime(2024, 1, 22),
    ]

    periods = detect_periodicity(times)

    assert "weekly" in periods


def test_detect_periodicity_insufficient_data():
    """Test periodicity detection with insufficient data."""
    times = [datetime(2024, 1, 1), datetime(2024, 1, 8)]

    periods = detect_periodicity(times)

    assert len(periods) == 0


def test_bin_time_references():
    """Test binning time references."""
    times = [
        datetime(2024, 1, 5),
        datetime(2024, 1, 15),
        datetime(2024, 2, 10),
    ]

    bins = bin_time_references(times, bin_size_days=30)

    assert len(bins) >= 1
    # Check that counts sum to total references
    total_count = sum(count for _, _, count in bins)
    assert total_count == len(times)
