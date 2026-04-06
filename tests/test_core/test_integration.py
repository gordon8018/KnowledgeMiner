# tests/test_core/test_integration.py
import pytest
import tempfile
import shutil
from src.wiki.core import WikiCore
from src.wiki.core.models import WikiPage, PageType
from src.core.relation_model import Relation, RelationType

@pytest.fixture
def wiki_core():
    """Create a WikiCore instance for testing."""
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)
    yield core
    # Clean up temp directory with error handling for Windows
    try:
        shutil.rmtree(temp_dir)
    except (PermissionError, OSError):
        # On Windows, sometimes files are locked
        import time
        time.sleep(0.1)
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass  # Temp dir will be cleaned up by OS

def test_wiki_core_initialization(wiki_core):
    """Test WikiCore initialization."""
    assert wiki_core.store is not None
    assert wiki_core.graph is not None
    assert wiki_core.query is not None

def test_complete_workflow(wiki_core):
    """Test complete workflow: create, search, graph query."""
    # Create a page
    page = WikiPage(
        id="test-topic",
        title="Test Topic",
        content="This is a test topic about machine learning.",
        page_type=PageType.TOPIC
    )
    wiki_core.create_page(page)

    # Search for the page
    results = wiki_core.search("machine learning")
    assert len(results) > 0
    assert any("test-topic" in r.id for r in results)

    # Get the page
    retrieved = wiki_core.get_page("test-topic")
    assert retrieved is not None
    assert retrieved.title == "Test Topic"

def test_graph_workflow(wiki_core):
    """Test graph operations workflow."""
    # Create pages
    wiki_core.create_page(WikiPage(
        id="A", title="Concept A", content="Content A", page_type=PageType.CONCEPT
    ))
    wiki_core.create_page(WikiPage(
        id="B", title="Concept B", content="Content B", page_type=PageType.CONCEPT
    ))

    # Add relation
    relation = Relation(
        id="relation-1",
        source_concept="A",
        target_concept="B",
        relation_type=RelationType.CAUSES,
        strength=0.8
    )
    wiki_core.add_relation(relation)

    # Query graph
    related = wiki_core.get_related_concepts("A")
    assert "B" in related
