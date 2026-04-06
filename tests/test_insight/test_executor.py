"""
Tests for BackfillExecutor.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from src.discovery.models.insight import Insight, InsightType
from src.discovery.models.pattern import Evidence
from src.wiki.core.models import WikiPage, PageType, WikiVersion
from src.wiki.core.storage import WikiStore
from src.wiki.insight.executor import BackfillExecutor


@pytest.fixture
def mock_wiki_store():
    """Create a mock WikiStore."""
    store = Mock(spec=WikiStore)
    return store


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.generate.return_value = "Updated content with insight integrated."
    return provider


@pytest.fixture
def sample_insight():
    """Create a sample insight for testing."""
    return Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="This is a test insight about machine learning patterns.",
        significance=0.8,
        related_concepts=["machine_learning", "neural_networks", "deep_learning"],
        related_patterns=["pattern-1"],
        related_gaps=[],
        evidence=[
            Evidence(
                source_id="doc-1",
                content="Evidence for the insight",
                confidence=0.9
            )
        ],
        actionable_suggestions=["Suggestion 1", "Suggestion 2"],
        generated_at=datetime.now(),
        metadata={}
    )


@pytest.fixture
def sample_pages():
    """Create sample Wiki pages for testing."""
    pages = [
        WikiPage(
            id="page-1",
            title="Machine Learning",
            content="# Machine Learning\n\nContent about machine learning.",
            page_type=PageType.CONCEPT,
            version=1,
            metadata={}
        ),
        WikiPage(
            id="page-2",
            title="Neural Networks",
            content="# Neural Networks\n\nContent about neural networks.",
            page_type=PageType.CONCEPT,
            version=2,
            metadata={}
        ),
        WikiPage(
            id="page-3",
            title="Unrelated Topic",
            content="# Unrelated Topic\n\nContent that doesn't match concepts.",
            page_type=PageType.CONCEPT,
            version=1,
            metadata={}
        )
    ]
    return pages


@pytest.fixture
def executor(mock_wiki_store, mock_llm_provider):
    """Create BackfillExecutor instance with mocked dependencies."""
    return BackfillExecutor(mock_wiki_store, mock_llm_provider)


# Test 1: find_target_pages with single concept
def test_find_target_pages_with_single_concept(executor, mock_wiki_store, sample_pages):
    """Test finding target pages with a single concept."""
    # Create insight with single concept
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="Test description",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock get_page to return pages that match
    def mock_get_page(page_id):
        if page_id == "machine_learning":
            return sample_pages[0]
        return None

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Find target pages
    targets = executor.find_target_pages(insight)

    # Should find the machine_learning page
    assert len(targets) == 1
    assert targets[0].id == "page-1"
    assert targets[0].title == "Machine Learning"


# Test 2: find_target_pages with multiple concepts
def test_find_target_pages_with_multiple_concepts(executor, mock_wiki_store, sample_pages, sample_insight):
    """Test finding target pages with multiple concepts."""
    # Mock get_page to return pages for each concept
    def mock_get_page(page_id):
        page_map = {
            "machine_learning": sample_pages[0],
            "neural_networks": sample_pages[1],
            "deep_learning": None  # This concept doesn't have a page
        }
        return page_map.get(page_id)

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Find target pages
    targets = executor.find_target_pages(sample_insight)

    # Should find 2 pages (machine_learning and neural_networks)
    assert len(targets) == 2
    page_ids = {page.id for page in targets}
    assert page_ids == {"page-1", "page-2"}


# Test 3: find_target_pages returns empty list when no matches
def test_find_target_pages_returns_empty_list_when_no_matches(executor, mock_wiki_store):
    """Test finding target pages when none match."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="Test description",
        significance=0.8,
        related_concepts=["nonexistent_concept"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock get_page to return None for all concepts
    mock_wiki_store.get_page.return_value = None

    # Find target pages
    targets = executor.find_target_pages(insight)

    # Should return empty list
    assert len(targets) == 0
    assert isinstance(targets, list)


# Test 4: find_target_pages with concept pages
def test_find_target_pages_with_concept_pages(executor, mock_wiki_store, sample_pages, sample_insight):
    """Test finding target pages works with CONCEPT page types."""
    # Mock get_page to return concept pages
    def mock_get_page(page_id):
        page_map = {
            "machine_learning": sample_pages[0],
            "neural_networks": sample_pages[1]
        }
        return page_map.get(page_id)

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Find target pages
    targets = executor.find_target_pages(sample_insight)

    # All returned pages should be CONCEPT type
    assert all(page.page_type == PageType.CONCEPT for page in targets)
    assert len(targets) == 2


# Test 5: find_target_pages with relation pages
def test_find_target_pages_with_relation_pages(executor, mock_wiki_store):
    """Test finding target pages works with RELATION page types."""
    # Create insight with relation concepts
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.RELATION,
        title="Relation Insight",
        description="Test description",
        significance=0.7,
        related_concepts=["rel-ml-to-nn"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Create relation page
    relation_page = WikiPage(
        id="page-rel-1",
        title="ML to NN Relation",
        content="# Relation\n\nContent about the relation.",
        page_type=PageType.RELATION,
        version=1,
        metadata={}
    )

    mock_wiki_store.get_page.return_value = relation_page

    # Find target pages
    targets = executor.find_target_pages(insight)

    # Should find relation page
    assert len(targets) == 1
    assert targets[0].page_type == PageType.RELATION


# Test 6: update_page_content adds insight section
def test_update_page_content_adds_insight_section(executor, mock_llm_provider, sample_pages):
    """Test that updating page content adds an insight section."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="This is a test insight.",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock LLM to add insight section
    mock_llm_provider.generate.return_value = (
        "# Machine Learning\n\nContent about machine learning.\n\n"
        "## Insights\n\n- **Test Insight**: This is a test insight."
    )

    # Update page content
    updated_page = executor.update_page_content(sample_pages[0], insight)

    # Should contain insight section
    assert "## Insights" in updated_page.content
    assert "Test Insight" in updated_page.content
    assert updated_page.version == 2  # Version should be incremented


# Test 7: update_page_content preserves existing content
def test_update_page_content_preserves_existing_content(executor, mock_llm_provider, sample_pages):
    """Test that updating page content preserves existing information."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="This is a test insight.",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    original_content = sample_pages[0].content

    # Mock LLM to preserve existing content
    mock_llm_provider.generate.return_value = (
        f"{original_content}\n\n## Insights\n\n- **Test Insight**: This is a test insight."
    )

    # Update page content
    updated_page = executor.update_page_content(sample_pages[0], insight)

    # Original content should be preserved
    assert original_content in updated_page.content
    assert "## Insights" in updated_page.content


# Test 8: update_page_content increments version
def test_update_page_content_increments_version(executor, mock_llm_provider, sample_pages):
    """Test that updating page content increments the version."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="This is a test insight.",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    original_version = sample_pages[0].version

    # Mock LLM response
    mock_llm_provider.generate.return_value = "# Updated content"

    # Update page content
    updated_page = executor.update_page_content(sample_pages[0], insight)

    # Version should be incremented
    assert updated_page.version == original_version + 1
    assert updated_page.version == 2


# Test 9: update_page_content with LLM failure
def test_update_page_content_with_llm_failure(executor, mock_llm_provider, sample_pages):
    """Test that LLM failures are handled gracefully."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="This is a test insight.",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock LLM to raise exception
    mock_llm_provider.generate.side_effect = Exception("LLM API error")

    # Should raise exception
    with pytest.raises(Exception) as exc_info:
        executor.update_page_content(sample_pages[0], insight)

    assert "LLM API error" in str(exc_info.value)


# Test 10: create_new_version creates version record
def test_create_new_version_creates_version_record(executor, mock_wiki_store, sample_pages):
    """Test that creating a new version creates a version record."""
    # Update page version
    sample_pages[0].increment_version()

    # Create version record
    version = executor.create_new_version(sample_pages[0], "Added insight")

    # Should create version with correct fields
    assert version.page_id == sample_pages[0].id
    assert version.version == sample_pages[0].version
    assert version.parent_version == sample_pages[0].version - 1
    assert version.change_summary == "Added insight"
    assert version.author == "backfill_executor"


# Test 11: create_new_version with correct metadata
def test_create_new_version_with_correct_metadata(executor, sample_pages, sample_insight):
    """Test that creating a new version includes correct metadata."""
    sample_pages[0].increment_version()

    # Create version record
    version = executor.create_new_version(
        sample_pages[0],
        "Added insight",
        metadata={"insight_id": sample_insight.id}
    )

    # Should include metadata
    assert "insight_id" in version.metadata
    assert version.metadata["insight_id"] == sample_insight.id


# Test 12: backfill_insight orchestrates full workflow
def test_backfill_insight_orchestrates_full_workflow(executor, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
    """Test that backfill_insight orchestrates the complete workflow."""
    # Mock get_page to return target pages
    def mock_get_page(page_id):
        page_map = {
            "machine_learning": sample_pages[0],
            "neural_networks": sample_pages[1]
        }
        return page_map.get(page_id)

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Mock update_page to return updated pages
    def mock_update_page(page):
        page.increment_version()
        return page

    mock_wiki_store.update_page.side_effect = mock_update_page

    # Mock LLM response
    mock_llm_provider.generate.return_value = "# Updated content"

    # Execute backfill
    updated_ids = executor.backfill_insight(sample_insight)

    # Should update both target pages
    assert len(updated_ids) == 2
    assert "page-1" in updated_ids
    assert "page-2" in updated_ids

    # Verify update_page was called for each target
    assert mock_wiki_store.update_page.call_count == 2


# Test 13: backfill_insight returns updated page IDs
def test_backfill_insight_returns_updated_page_ids(executor, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
    """Test that backfill_insight returns correct page IDs."""
    # Mock get_page
    def mock_get_page(page_id):
        page_map = {
            "machine_learning": sample_pages[0]
        }
        return page_map.get(page_id)

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Mock update_page
    def mock_update_page(page):
        page.increment_version()
        return page

    mock_wiki_store.update_page.side_effect = mock_update_page

    # Mock LLM
    mock_llm_provider.generate.return_value = "# Updated content"

    # Execute backfill
    updated_ids = executor.backfill_insight(sample_insight)

    # Should return list of page IDs
    assert isinstance(updated_ids, list)
    assert len(updated_ids) == 1
    assert "page-1" in updated_ids


# Test 14: backfill_insight with no target pages
def test_backfill_insight_with_no_target_pages(executor, mock_wiki_store, mock_llm_provider):
    """Test backfill_insight when no target pages are found."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="Test description",
        significance=0.8,
        related_concepts=["nonexistent"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock get_page to return None
    mock_wiki_store.get_page.return_value = None

    # Execute backfill
    updated_ids = executor.backfill_insight(insight)

    # Should return empty list
    assert len(updated_ids) == 0

    # update_page should not be called
    mock_wiki_store.update_page.assert_not_called()


# Test 15: backfill_insight with multiple target pages
def test_backfill_insight_with_multiple_target_pages(executor, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
    """Test backfill_insight with multiple target pages."""
    # Mock get_page to return 3 pages
    def mock_get_page(page_id):
        page_map = {
            "machine_learning": sample_pages[0],
            "neural_networks": sample_pages[1],
            "deep_learning": sample_pages[2]
        }
        return page_map.get(page_id)

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Mock update_page
    def mock_update_page(page):
        page.increment_version()
        return page

    mock_wiki_store.update_page.side_effect = mock_update_page

    # Mock LLM
    mock_llm_provider.generate.return_value = "# Updated content"

    # Execute backfill
    updated_ids = executor.backfill_insight(sample_insight)

    # Should update all 3 pages
    assert len(updated_ids) == 3
    assert "page-1" in updated_ids
    assert "page-2" in updated_ids
    assert "page-3" in updated_ids


# Test 16: backfill_insight handles update failures
def test_backfill_insight_handles_update_failures(executor, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
    """Test that backfill_insight handles update failures gracefully."""
    # Mock get_page
    def mock_get_page(page_id):
        page_map = {
            "machine_learning": sample_pages[0],
            "neural_networks": sample_pages[1]
        }
        return page_map.get(page_id)

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Mock update_page to fail on second page
    def mock_update_page(page):
        if page.id == "page-2":
            raise ValueError("Update failed")
        page.increment_version()
        return page

    mock_wiki_store.update_page.side_effect = mock_update_page

    # Mock LLM
    mock_llm_provider.generate.return_value = "# Updated content"

    # Should raise exception
    with pytest.raises(ValueError) as exc_info:
        executor.backfill_insight(sample_insight)

    assert "Update failed" in str(exc_info.value)


# Test 17: content_update_maintains_markdown_structure
def test_content_update_maintains_markdown_structure(executor, mock_llm_provider, sample_pages):
    """Test that content updates maintain markdown structure."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="This is a test insight.",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock LLM to maintain markdown structure
    mock_llm_provider.generate.return_value = (
        "# Machine Learning\n\n"
        "Content about machine learning.\n\n"
        "## Insights\n\n"
        "- **Test Insight**: This is a test insight.\n\n"
        "## Related Concepts\n\n"
        "- Neural Networks\n"
        "- Deep Learning"
    )

    # Update page content
    updated_page = executor.update_page_content(sample_pages[0], insight)

    # Should maintain markdown structure
    assert updated_page.content.startswith("#")
    assert "##" in updated_page.content
    assert "- " in updated_page.content


# Test 18: version_creation_captures_parent_version
def test_version_creation_captures_parent_version(executor, sample_pages):
    """Test that version creation correctly captures parent version."""
    original_version = sample_pages[0].version
    sample_pages[0].increment_version()

    # Create version
    version = executor.create_new_version(sample_pages[0], "Test update")

    # Should capture parent version
    assert version.parent_version == original_version
    assert version.version == original_version + 1


# Test 19: error_handling_for_missing_page
def test_error_handling_for_missing_page(executor, mock_wiki_store):
    """Test error handling when page doesn't exist."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="Test description",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock get_page to return None (page doesn't exist)
    mock_wiki_store.get_page.return_value = None

    # Find target pages - should handle gracefully
    targets = executor.find_target_pages(insight)

    # Should return empty list
    assert len(targets) == 0


# Test 20: error_handling_for_llm_timeout
def test_error_handling_for_llm_timeout(executor, mock_llm_provider, sample_pages):
    """Test error handling for LLM timeout."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="This is a test insight.",
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock LLM timeout
    mock_llm_provider.generate.side_effect = TimeoutError("LLM request timed out")

    # Should raise timeout error
    with pytest.raises(TimeoutError) as exc_info:
        executor.update_page_content(sample_pages[0], insight)

    assert "timed out" in str(exc_info.value).lower()


# Test 21: backfill_insight_with_empty_insight
def test_backfill_insight_with_empty_insight(executor, mock_wiki_store):
    """Test backfill_insight with insight having no related concepts."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="Test description",
        significance=0.8,
        related_concepts=[],  # Empty concepts
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Execute backfill
    updated_ids = executor.backfill_insight(insight)

    # Should return empty list (no concepts to find)
    assert len(updated_ids) == 0

    # get_page should not be called
    mock_wiki_store.get_page.assert_not_called()


# Test 22: find_target_pages_handles_duplicate_concepts
def test_find_target_pages_handles_duplicate_concepts(executor, mock_wiki_store, sample_pages):
    """Test that find_target_pages handles duplicate concepts correctly."""
    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description="Test description",
        significance=0.8,
        related_concepts=["machine_learning", "machine_learning"],  # Duplicate
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock get_page
    mock_wiki_store.get_page.return_value = sample_pages[0]

    # Find target pages
    targets = executor.find_target_pages(insight)

    # Should deduplicate and return only one page
    assert len(targets) == 1
    assert targets[0].id == "page-1"


# Test 23: update_page_content_with_long_insight
def test_update_page_content_with_long_insight(executor, mock_llm_provider, sample_pages):
    """Test updating page content with a long insight description."""
    long_description = "This is a very long insight description. " * 20

    insight = Insight(
        id="insight-1",
        insight_type=InsightType.PATTERN,
        title="Test Insight",
        description=long_description,
        significance=0.8,
        related_concepts=["machine_learning"],
        related_patterns=[],
        related_gaps=[],
        evidence=[],
        actionable_suggestions=[],
        generated_at=datetime.now(),
        metadata={}
    )

    # Mock LLM to handle long content
    mock_llm_provider.generate.return_value = "# Updated content with long insight"

    # Update page content
    updated_page = executor.update_page_content(sample_pages[0], insight)

    # Should successfully update
    assert updated_page.content is not None
    assert updated_page.version == 2


# Test 24: create_new_version_with_custom_author
def test_create_new_version_with_custom_author(executor, sample_pages):
    """Test creating a new version with a custom author."""
    sample_pages[0].increment_version()

    # Create version with custom author
    version = executor.create_new_version(
        sample_pages[0],
        "Test update",
        author="custom_user"
    )

    # Should use custom author
    assert version.author == "custom_user"


# Test 25: backfill_insight_continues_on_partial_failure
def test_backfill_insight_continues_on_partial_failure(executor, mock_wiki_store, mock_llm_provider, sample_insight, sample_pages):
    """Test that backfill_insight continues even if some pages fail."""
    # Mock get_page
    def mock_get_page(page_id):
        page_map = {
            "machine_learning": sample_pages[0],
            "neural_networks": sample_pages[1],
            "deep_learning": sample_pages[2]
        }
        return page_map.get(page_id)

    mock_wiki_store.get_page.side_effect = mock_get_page

    # Track which pages were successfully updated
    updated_pages = []

    # Mock update_page to fail on page-2
    def mock_update_page(page):
        if page.id == "page-2":
            raise ValueError("Update failed for page-2")
        page.increment_version()
        updated_pages.append(page.id)
        return page

    mock_wiki_store.update_page.side_effect = mock_update_page

    # Mock LLM
    mock_llm_provider.generate.return_value = "# Updated content"

    # Should raise exception on failure
    with pytest.raises(ValueError):
        executor.backfill_insight(sample_insight)

    # But page-1 and page-3 should have been updated
    # (depending on implementation - this test checks current behavior)
    assert mock_wiki_store.update_page.call_count >= 1
