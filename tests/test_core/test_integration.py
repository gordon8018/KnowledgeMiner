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

def test_comprehensive_multi_page_workflow(wiki_core):
    """Test comprehensive workflow with multiple pages, updates, and graph paths."""
    # Create multiple pages
    wiki_core.create_page(WikiPage(
        id="neural-network",
        title="Neural Network",
        content="A neural network is a network of neurons.",
        page_type=PageType.CONCEPT
    ))
    wiki_core.create_page(WikiPage(
        id="deep-learning",
        title="Deep Learning",
        content="Deep learning uses neural networks.",
        page_type=PageType.TOPIC
    ))
    wiki_core.create_page(WikiPage(
        id="machine-learning",
        title="Machine Learning",
        content="Machine learning includes deep learning.",
        page_type=PageType.TOPIC
    ))

    # Update a page
    updated_page = WikiPage(
        id="neural-network",
        title="Neural Network",
        content="A neural network is a computational model based on biological neural networks.",
        page_type=PageType.CONCEPT
    )
    wiki_core.update_page(updated_page)

    # Verify update
    retrieved = wiki_core.get_page("neural-network")
    assert "computational model" in retrieved.content

    # Add multiple relations forming a chain
    wiki_core.add_relation(Relation(
        id="rel-1",
        source_concept="neural-network",
        target_concept="deep-learning",
        relation_type=RelationType.CONTAINED_IN,
        strength=0.9
    ))
    wiki_core.add_relation(Relation(
        id="rel-2",
        source_concept="deep-learning",
        target_concept="machine-learning",
        relation_type=RelationType.CONTAINED_IN,
        strength=0.95
    ))

    # Test search with pagination
    results = wiki_core.search("learning", limit=2)
    assert len(results) <= 2
    results_ids = [r.id for r in results]
    assert "deep-learning" in results_ids or "machine-learning" in results_ids

    # Test graph path finding
    path = wiki_core.find_shortest_path("neural-network", "machine-learning")
    assert path is not None
    assert len(path) >= 2
    assert "neural-network" in path
    assert "machine-learning" in path

    # Test related concepts chain
    related_to_nn = wiki_core.get_related_concepts("neural-network")
    assert "deep-learning" in related_to_nn
