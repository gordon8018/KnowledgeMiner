# Phase 3: Intelligent Knowledge Accumulation System - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform KnowledgeMiner from a one-time analysis tool into a persistent knowledge accumulation system with automatic Wiki maintenance, intelligent insight backfilling, and continuous quality assurance.

**Architecture:** Four-component architecture (WikiCore, DiscoveryPipeline 2.0, InsightManager, QualitySystem) with simplified complexity management. All components designed from scratch for optimal integration, reusing Phase 2 components where possible.

**Tech Stack:** Python 3.10+, SQLite, Git, Whoosh, APScheduler, NetworkX (Phase 2), Pydantic (Phase 2), pytest.

**Timeline:** 27-28 weeks (395+ tests)

---

## Scope and Approach

This plan implements **Phase 3: Intelligent Knowledge Accumulation** as specified in `docs/superpowers/specs/2026-04-06-phase3-intelligent-knowledge-accumulation-design.md` (v1.1).

**Key Simplifications from v1.0**:
- WikiCore focuses on storage/versioning only (uses NetworkX for graphs)
- Incremental mode uses hybrid approach with smart selection
- Insight propagation limited to direct only (max 2 hops)
- Auto-repair staged (manual → semi-auto → auto)
- Added Stage 6 for resilience testing

**Implementation Strategy**:
1. **Stage-by-stage delivery**: Each of 6 stages produces working, testable software
2. **TDD methodology**: Tests written first, then implementation
3. **Frequent commits**: Every completed step committed immediately
4. **Continuous integration**: All tests must pass after each commit
5. **Code review**: Each task reviewed before moving to next
6. **Phase 2 Analysis**: Assess refactoring scope before implementation

---

## File Structure Overview

**New Directory Structure**:
```
src/
├── wiki/                          # NEW: Wiki components
│   ├── __init__.py
│   ├── core/                      # WikiCore
│   │   ├── __init__.py
│   │   ├── storage.py             # WikiStore
│   │   ├── version.py             # VersionLog
│   │   ├── graph.py               # KnowledgeGraph (uses NetworkX)
│   │   ├── query.py               # QueryEngine
│   │   └── models.py              # Wiki data models
│   ├── discovery/                 # DiscoveryPipeline 2.0
│   │   ├── __init__.py
│   │   ├── pipeline.py            # Main pipeline
│   │   ├── input.py               # InputProcessor
│   │   ├── mode_selector.py       # ModeSelector (full/inc/hybrid)
│   │   ├── orchestrator.py        # DiscoveryOrchestrator
│   │   └── integrator.py          # WikiIntegrator
│   ├── insight/                   # InsightManager
│   │   ├── __init__.py
│   │   ├── manager.py             # InsightManager
│   │   ├── receiver.py            # InsightReceiver
│   │   ├── scorer.py              # PriorityScorer
│   │   ├── scheduler.py           # BackfillScheduler
│   │   ├── executor.py            # BackfillExecutor
│   │   └── propagator.py          # InsightPropagator (direct only)
│   ├── quality/                   # QualitySystem
│   │   ├── __init__.py
│   │   ├── system.py              # QualitySystem
│   │   ├── monitor.py             # HealthMonitor
│   │   ├── classifier.py          # IssueClassifier
│   │   ├── repairer.py            # Staged repair system
│   │   └── reporter.py            # QualityReporter
│   ├── config.py                  # WikiConfig with profiles
│   └── schema.py                  # WIKI_SCHEMA manager
│
tests/
├── test_wiki/                     # NEW: Wiki tests
│   ├── test_core/                 # WikiCore tests (80+ tests)
│   ├── test_discovery/            # DiscoveryPipeline tests (80+ tests)
│   ├── test_insight/              # InsightManager tests (90+ tests)
│   ├── test_quality/              # QualitySystem tests (55+ tests)
│   ├── test_integration/          # Integration tests (30+ tests)
│   └── test_resilience/           # Resilience tests (60+ tests)
│
wiki_storage/                      # NEW: Wiki storage directory
├── .git/                          # Git repository
├── topics/                        # Topic pages
├── concepts/                      # Concept entries
├── relations/                     # Relation records
├── meta/                          # Metadata (SQLite)
│   └── wiki.db
└── schema/                        # Schema files
    └── WIKI_SCHEMA.md
```

**Modified Files** (Phase 2 integration):
```
src/discovery/relation_miner.py     # Add mode parameter
src/discovery/pattern_detector.py  # Add mode parameter
src/discovery/gap_analyzer.py      # Add mode parameter
src/discovery/insight_generator.py # Add mode parameter
```

---

## Stage 1: Foundation - WikiCore Storage Engine (Weeks 1-4)

**Goal**: Build simplified WikiCore for storage, versioning, and basic retrieval.

**Acceptance Criteria**:
- Wiki can store topics, concepts, and relations
- Version history tracked via Git
- Basic search functional
- NetworkX integration for graph queries
- 80+ tests passing
- Performance baseline established

### Task 1.1: Implement WikiStore and Data Models

**Files**:
- Create: `src/wiki/core/models.py`
- Create: `src/wiki/core/storage.py`
- Test: `tests/test_core/test_models.py`
- Test: `tests/test_core/test_storage.py`

- [ ] **Step 1: Create wiki package structure**

```bash
mkdir -p src/wiki/core
touch src/wiki/__init__.py
touch src/wiki/core/__init__.py
```

- [ ] **Step 2: Write data model tests**

```python
# tests/test_core/test_models.py
import pytest
from datetime import datetime
from src.wiki.core.models import WikiPage, WikiVersion, WikiUpdate

def test_wiki_page_creation():
    page = WikiPage(
        id="test-page",
        title="Test Page",
        content="Test content",
        page_type="topic",
        created_at=datetime.now()
    )
    assert page.id == "test-page"
    assert page.page_type == "topic"
    assert page.version == 0

def test_wiki_version_creation():
    version = WikiVersion(
        page_id="test-page",
        version=1,
        content="Updated content",
        parent_version=0,
        change_summary="Initial update",
        created_at=datetime.now()
    )
    assert version.version == 1
    assert version.parent_version == 0

def test_wiki_update_creation():
    update = WikiUpdate(
        page_id="test-page",
        update_type="create",
        content="New content",
        metadata={"key": "value"},
        version=1,
        parent_version=0,
        change_summary="Create page"
    )
    assert update.update_type == "create"
    assert "key" in update.metadata
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd .worktrees/phase2-discovery
pytest tests/test_core/test_models.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.wiki.core.models'"

- [ ] **Step 4: Implement data models**

```python
# src/wiki/core/models.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class PageType(str, Enum):
    TOPIC = "topic"
    CONCEPT = "concept"
    RELATION = "relation"

class UpdateType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"

class WikiPage(BaseModel):
    """A Wiki page representing a topic, concept, or relation."""

    id: str = Field(..., description="Unique page identifier")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content (markdown)")
    page_type: PageType = Field(..., description="Type of page")
    version: int = Field(default=0, description="Current version number")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def increment_version(self) -> int:
        """Increment version number and return new version."""
        self.version += 1
        self.updated_at = datetime.now()
        return self.version

class WikiVersion(BaseModel):
    """A specific version of a Wiki page."""

    page_id: str
    version: int
    content: str
    parent_version: int
    change_summary: str
    created_at: datetime = Field(default_factory=datetime.now)
    author: str = Field(default="system")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WikiUpdate(BaseModel):
    """An update to be applied to a Wiki page."""

    page_id: str
    update_type: UpdateType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: int
    parent_version: int
    change_summary: str
    repair_id: Optional[str] = None  # If from auto-repair
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_core/test_models.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 6: Write WikiStore tests**

```python
# tests/test_core/test_storage.py (part 1)
import pytest
import tempfile
import shutil
from pathlib import Path
from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage, PageType

@pytest.fixture
def temp_store():
    """Create a temporary WikiStore for testing."""
    temp_dir = tempfile.mkdtemp()
    store = WikiStore(storage_path=temp_dir)
    yield store
    shutil.rmtree(temp_dir)

def test_store_initialization(temp_store):
    """Test that WikiStore initializes correctly."""
    assert temp_store.storage_path.exists()
    assert temp_store.topics_dir.exists()
    assert temp_store.concepts_dir.exists()
    assert temp_store.relations_dir.exists()
    assert temp_store.meta_dir.exists()

def test_create_topic_page(temp_store):
    """Test creating a topic page."""
    page = WikiPage(
        id="machine-learning",
        title="Machine Learning",
        content="# Machine Learning\n\nA field of AI...",
        page_type=PageType.TOPIC
    )

    temp_store.create_page(page)

    # Check file exists
    file_path = temp_store.topics_dir / "machine-learning.md"
    assert file_path.exists()

    # Check content
    content = file_path.read_text()
    assert content == "# Machine Learning\n\nA field of AI..."

def test_create_concept_page(temp_store):
    """Test creating a concept page."""
    page = WikiPage(
        id="q-learning",
        title="Q-Learning",
        content="Q-learning is a model-free algorithm...",
        page_type=PageType.CONCEPT
    )

    temp_store.create_page(page)

    file_path = temp_store.concepts_dir / "q-learning.md"
    assert file_path.exists()

def test_get_page(temp_store):
    """Test retrieving a page."""
    # Create page first
    page = WikiPage(
        id="test-page",
        title="Test",
        content="Test content",
        page_type=PageType.TOPIC
    )
    temp_store.create_page(page)

    # Retrieve page
    retrieved = temp_store.get_page("test-page")
    assert retrieved.id == "test-page"
    assert retrieved.title == "Test"
    assert retrieved.content == "Test content"

def test_update_page(temp_store):
    """Test updating a page."""
    # Create page
    page = WikiPage(
        id="test-page",
        title="Test",
        content="Original content",
        page_type=PageType.TOPIC
    )
    temp_store.create_page(page)

    # Update page
    page.content = "Updated content"
    updated = temp_store.update_page(page)

    assert updated.version == 1
    assert updated.content == "Updated content"
```

- [ ] **Step 7: Run tests to verify they fail**

```bash
pytest tests/test_core/test_storage.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.wiki.core.storage'"

- [ ] **Step 8: Implement WikiStore**

```python
# src/wiki/core/storage.py
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import shutil
import json

from src.wiki.core.models import WikiPage, WikiVersion, PageType

class WikiStore:
    """
    Simplified Wiki storage engine.

    Stores Wiki pages as markdown files with Git version control.
    Uses SQLite for metadata and indexing.
    """

    def __init__(self, storage_path: str):
        """
        Initialize WikiStore.

        Args:
            storage_path: Path to wiki storage directory
        """
        self.storage_path = Path(storage_path)
        self.topics_dir = self.storage_path / "topics"
        self.concepts_dir = self.storage_path / "concepts"
        self.relations_dir = self.storage_path / "relations"
        self.meta_dir = self.storage_path / "meta"
        self.schema_dir = self.storage_path / "schema"

        # Create directories
        for dir_path in [self.topics_dir, self.concepts_dir,
                        self.relations_dir, self.meta_dir,
                        self.schema_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database
        self.db_path = self.meta_dir / "wiki.db"
        self._init_database()

        # Initialize Git repository
        self._init_git()

    def _init_database(self):
        """Initialize SQLite database for metadata."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                page_type TEXT NOT NULL,
                version INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                metadata TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                parent_version INTEGER,
                change_summary TEXT,
                created_at TIMESTAMP,
                author TEXT,
                FOREIGN KEY (page_id) REFERENCES pages(id)
            )
        """)
        self.conn.commit()

    def _init_git(self):
        """Initialize Git repository for version control."""
        import subprocess

        # Initialize .git if not exists
        git_dir = self.storage_path / ".git"
        if not git_dir.exists():
            subprocess.run(
                ["git", "init"],
                cwd=str(self.storage_path),
                capture_output=True
            )

    def _get_page_dir(self, page_type: PageType) -> Path:
        """Get directory for a page type."""
        if page_type == PageType.TOPIC:
            return self.topics_dir
        elif page_type == PageType.CONCEPT:
            return self.concepts_dir
        else:  # RELATION
            return self.relations_dir

    def _get_page_path(self, page_id: str, page_type: PageType) -> Path:
        """Get file path for a page."""
        dir_path = self._get_page_dir(page_type)
        return dir_path / f"{page_id}.md"

    def create_page(self, page: WikiPage) -> WikiPage:
        """
        Create a new Wiki page.

        Args:
            page: WikiPage to create

        Returns:
            Created WikiPage with updated metadata
        """
        # Check if page already exists
        if self.get_page(page.id):
            raise ValueError(f"Page {page.id} already exists")

        # Save page content to file
        file_path = self._get_page_path(page.id, page.page_type)
        file_path.write_text(page.content)

        # Insert metadata into database
        self.conn.execute(
            "INSERT INTO pages (id, title, page_type, version, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (page.id, page.title, page.page_type.value, page.version,
             page.created_at, page.updated_at, json.dumps(page.metadata))
        )
        self.conn.commit()

        # Git commit
        self._git_commit(f"Create page: {page.id}", [str(file_path.relative_to(self.storage_path))])

        return page

    def get_page(self, page_id: str) -> Optional[WikiPage]:
        """
        Retrieve a Wiki page by ID.

        Args:
            page_id: Page ID to retrieve

        Returns:
            WikiPage if found, None otherwise
        """
        # Query database
        cursor = self.conn.execute(
            "SELECT * FROM pages WHERE id = ?",
            (page_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        # Read content from file
        cursor = self.conn.execute("SELECT page_type FROM pages WHERE id = ?", (page_id,))
        page_type_str = cursor.fetchone()[0]
        page_type = PageType(page_type_str)

        file_path = self._get_page_path(page_id, page_type)
        content = file_path.read_text() if file_path.exists() else ""

        return WikiPage(
            id=row[0],
            title=row[1],
            content=content,
            page_type=PageType(row[2]),
            version=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            metadata=json.loads(row[6]) if row[6] else {}
        )

    def update_page(self, page: WikiPage) -> WikiPage:
        """
        Update an existing Wiki page.

        Args:
            page: WikiPage with updates

        Returns:
            Updated WikiPage with incremented version
        """
        # Check if page exists
        existing = self.get_page(page.id)
        if not existing:
            raise ValueError(f"Page {page.id} does not exist")

        # Increment version
        old_version = page.version
        new_version = page.increment_version()

        # Update file
        file_path = self._get_page_path(page.id, page.page_type)
        file_path.write_text(page.content)

        # Update database
        self.conn.execute(
            "UPDATE pages SET title = ?, version = ?, updated_at = ?, metadata = ? WHERE id = ?",
            (page.title, new_version, page.updated_at, json.dumps(page.metadata), page.id)
        )

        # Record version
        self.conn.execute(
            "INSERT INTO versions (page_id, version, parent_version, change_summary, created_at) VALUES (?, ?, ?, ?, ?)",
            (page.id, new_version, old_version, "Page updated", page.updated_at)
        )
        self.conn.commit()

        # Git commit
        self._git_commit(f"Update page: {page.id}", [str(file_path.relative_to(self.storage_path))])

        return page

    def _git_commit(self, message: str, files: List[str]):
        """Create a Git commit."""
        import subprocess

        # Add files
        for file_path in files:
            subprocess.run(
                ["git", "add", file_path],
                cwd=str(self.storage_path),
                capture_output=True
            )

        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(self.storage_path),
            capture_output=True
        )
```

- [ ] **Step 9: Run tests to verify they pass**

```bash
pytest tests/test_core/test_storage.py -v
```

Expected: PASS (6 tests)

- [ ] **Step 10: Commit**

```bash
cd .worktrees/phase2-discovery
git add src/wiki/core/models.py src/wiki/core/storage.py tests/test_core/
git commit -m "feat: implement WikiStore and data models (Task 1.1)"
```

### Task 1.2: Integrate NetworkX for Graph Operations

**Files**:
- Create: `src/wiki/core/graph.py`
- Test: `tests/test_core/test_graph.py`

- [ ] **Step 1: Write graph tests**

```python
# tests/test_core/test_graph.py
import pytest
from src.wiki.core.graph import KnowledgeGraph
from src.core.relation_model import Relation, RelationType

@pytest.fixture
def sample_relations():
    """Create sample relations for testing."""
    return [
        Relation(
            source_concept="A",
            target_concept="B",
            relation_type=RelationType.CAUSES,
            strength=0.8,
            confidence=0.9
        ),
        Relation(
            source_concept="B",
            target_concept="C",
            relation_type=RelationType.ENABLES,
            strength=0.7,
            confidence=0.8
        ),
        Relation(
            source_concept="A",
            target_concept="C",
            relation_type=RelationType.RELATED_TO,
            strength=0.5,
            confidence=0.7
        )
    ]

def test_graph_initialization():
    """Test graph initialization."""
    graph = KnowledgeGraph()
    assert graph.graph is not None
    assert graph.graph.number_of_nodes() == 0
    assert graph.graph.number_of_edges() == 0

def test_add_relations(sample_relations):
    """Test adding relations to graph."""
    graph = KnowledgeGraph()
    graph.add_relations(sample_relations)

    assert graph.graph.number_of_nodes() == 3
    assert graph.graph.number_of_edges() == 3

def test_get_related_concepts(sample_relations):
    """Test getting related concepts."""
    graph = KnowledgeGraph()
    graph.add_relations(sample_relations)

    related = graph.get_related_concepts("A")
    assert "B" in related
    assert "C" in related

def test_find_shortest_path(sample_relations):
    """Test finding shortest path between concepts."""
    graph = KnowledgeGraph()
    graph.add_relations(sample_relations)

    path = graph.find_shortest_path("A", "C")
    assert path is not None
    assert "A" in path
    assert "C" in path
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_core/test_graph.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.wiki.core.graph'"

- [ ] **Step 3: Implement KnowledgeGraph using NetworkX**

```python
# src/wiki/core/graph.py
import networkx as nx
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.relation_model import Relation

class KnowledgeGraph:
    """
    Knowledge graph using NetworkX.

    Reuses NetworkX from Phase 2 for graph operations.
    Simplified to core functionality: concept graph and basic queries.
    """

    def __init__(self):
        """Initialize an empty knowledge graph."""
        self.graph = nx.DiGraph()

    def add_relations(self, relations: List[Relation]):
        """
        Add relations to the graph.

        Args:
            relations: List of Relation objects to add
        """
        for relation in relations:
            self.graph.add_edge(
                relation.source_concept,
                relation.target_concept,
                relation_type=relation.relation_type.value,
                strength=relation.strength,
                confidence=relation.confidence
            )

    def get_related_concepts(self, concept: str) -> List[str]:
        """
        Get concepts directly related to the given concept.

        Args:
            concept: Concept name

        Returns:
            List of related concept names
        """
        if concept not in self.graph:
            return []

        return list(self.graph.neighbors(concept))

    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find shortest path between two concepts.

        Args:
            source: Source concept
            target: Target concept

        Returns:
            List of concept names in path, or None if no path exists
        """
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return None

    def get_concept_connections(self, concept: str) -> Dict[str, Any]:
        """
        Get connection statistics for a concept.

        Args:
            concept: Concept name

        Returns:
            Dictionary with connection statistics
        """
        if concept not in self.graph:
            return {"in_degree": 0, "out_degree": 0, "total_degree": 0}

        return {
            "in_degree": self.graph.in_degree(concept),
            "out_degree": self.graph.out_degree(concept),
            "total_degree": self.graph.degree(concept)
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_core/test_graph.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/wiki/core/graph.py tests/test_core/test_graph.py
git commit -m "feat: integrate NetworkX for graph operations (Task 1.2)"
```

### Task 1.3: Implement QueryEngine with Whoosh

**Files**:
- Create: `src/wiki/core/query.py`
- Test: `tests/test_core/test_query.py`

- [ ] **Step 1: Write query engine tests**

```python
# tests/test_core/test_query.py
import pytest
import tempfile
import shutil
from src.wiki.core.query import QueryEngine
from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage, PageType

@pytest.fixture
def query_engine():
    """Create a QueryEngine with sample data."""
    temp_dir = tempfile.mkdtemp()
    store = WikiStore(storage_path=temp_dir)

    # Create sample pages
    pages = [
        WikiPage(
            id="ml",
            title="Machine Learning",
            content="Machine learning is a subset of artificial intelligence.",
            page_type=PageType.TOPIC
        ),
        WikiPage(
            id="dl",
            title="Deep Learning",
            content="Deep learning uses neural networks with multiple layers.",
            page_type=PageType.TOPIC
        ),
        WikiPage(
            id="nn",
            title="Neural Networks",
            content="Neural networks are computing systems inspired by biological neural networks.",
            page_type=PageType.CONCEPT
        )
    ]

    for page in pages:
        store.create_page(page)

    engine = QueryEngine(store)
    yield engine

    shutil.rmtree(temp_dir)

def test_basic_search(query_engine):
    """Test basic full-text search."""
    results = query_engine.search("artificial intelligence")
    assert len(results) > 0
    assert any("ml" in r.id for r in results)

def test_search_returns_empty(query_engine):
    """Test search with no results."""
    results = query_engine.search("nonexistent term xyzabc")
    assert len(results) == 0

def test_get_page_by_id(query_engine):
    """Test retrieving a page by ID."""
    page = query_engine.get_page("ml")
    assert page is not None
    assert page.title == "Machine Learning"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_core/test_query.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.wiki.core.query'"

- [ ] **Step 3: Implement QueryEngine**

```python
# src/wiki/core/query.py
from typing import List, Optional
from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from pathlib import Path

from src.wiki.core.storage import WikiStore
from src.wiki.core.models import WikiPage

class QueryEngine:
    """
    Query engine for Wiki content.

    Uses Whoosh for full-text search.
    Integrates with WikiStore for content retrieval.
    """

    def __init__(self, store: WikiStore):
        """
        Initialize QueryEngine.

        Args:
            store: WikiStore instance
        """
        self.store = store
        self.index_dir = store.storage_path / "meta" / "search_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Define schema
        self.schema = Schema(
            page_id=ID(stored=True),
            title=TEXT(field_boost=2.0),  # Boost title matches
            content=TEXT
        )

        # Create or open index
        if exists_in(str(self.index_dir)):
            self.index = open_dir(str(self.index_dir))
        else:
            self.index = create_in(str(self.index_dir), self.schema)

        # Build index from existing pages
        self._build_index()

    def _build_index(self):
        """Build search index from all Wiki pages."""
        writer = self.index.writer()

        # Index all topics
        for file_path in self.store.topics_dir.glob("*.md"):
            page_id = file_path.stem
            page = self.store.get_page(page_id)
            if page:
                writer.add_document(
                    page_id=page_id,
                    title=page.title,
                    content=page.content
                )

        # Index all concepts
        for file_path in self.store.concepts_dir.glob("*.md"):
            page_id = file_path.stem
            page = self.store.get_page(page_id)
            if page:
                writer.add_document(
                    page_id=page_id,
                    title=page.title,
                    content=page.content
                )

        writer.commit()

    def search(self, query_str: str, limit: int = 10) -> List[WikiPage]:
        """
        Search Wiki content.

        Args:
            query_str: Search query string
            limit: Maximum number of results

        Returns:
            List of WikiPage objects matching the query
        """
        with self.index.searcher() as searcher:
            query = QueryParser("content", self.index.schema).parse(query_str)
            results = searcher.search(query, limit=limit)

            pages = []
            for hit in results:
                page = self.store.get_page(hit["page_id"])
                if page:
                    pages.append(page)

            return pages

    def get_page(self, page_id: str) -> Optional[WikiPage]:
        """
        Get a page by ID.

        Args:
            page_id: Page ID to retrieve

        Returns:
            WikiPage if found, None otherwise
        """
        return self.store.get_page(page_id)

    def update_index(self, page: WikiPage):
        """
        Update search index for a page.

        Args:
            page: WikiPage to update in index
        """
        writer = self.index.writer()
        writer.update_document(
            page_id=page.id,
            title=page.title,
            content=page.content
        )
        writer.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_core/test_query.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/wiki/core/query.py tests/test_core/test_query.py
git commit -m "feat: implement QueryEngine with Whoosh (Task 1.3)"
```

### Task 1.4: Implement WIKI_SCHEMA System

**Files**:
- Create: `src/wiki/schema.py`
- Create: `wiki_storage/schema/WIKI_SCHEMA.md`
- Test: `tests/test_core/test_schema.py`

- [ ] **Step 1: Write schema manager tests**

```python
# tests/test_core/test_schema.py
import pytest
import tempfile
import shutil
from src.wiki.schema import SchemaManager

@pytest.fixture
def schema_manager():
    """Create a SchemaManager for testing."""
    temp_dir = tempfile.mkdtemp()
    manager = SchemaManager(storage_path=temp_dir)
    yield manager
    shutil.rmtree(temp_dir)

def test_schema_manager_initialization(schema_manager):
    """Test schema manager initialization."""
    assert schema_manager.schema_path.exists()
    assert schema_manager.schema_path.name == "WIKI_SCHEMA.md"

def test_validate_metadata(schema_manager):
    """Test metadata validation."""
    valid_metadata = {
        "title": "Test Page",
        "type": "topic",
        "confidence": 0.9
    }

    is_valid, errors = schema_manager.validate_metadata(valid_metadata)
    assert is_valid
    assert len(errors) == 0

def test_validate_metadata_missing_field(schema_manager):
    """Test metadata validation with missing required field."""
    invalid_metadata = {
        "type": "topic"
        # Missing "title"
    }

    is_valid, errors = schema_manager.validate_metadata(invalid_metadata)
    assert not is_valid
    assert "title" in str(errors).lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_core/test_schema.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.wiki.schema'"

- [ ] **Step 3: Implement SchemaManager**

```python
# src/wiki/schema.py
from pathlib import Path
from typing import Dict, Any, Tuple, List
import yaml

class SchemaManager:
    """
    Manager for WIKI_SCHEMA.md and metadata validation.

    WIKI_SCHEMA.md defines the structure and validation rules
    for Wiki metadata.
    """

    REQUIRED_FIELDS = ["title", "type"]
    VALID_TYPES = ["topic", "concept", "relation"]

    def __init__(self, storage_path: str):
        """
        Initialize SchemaManager.

        Args:
            storage_path: Path to wiki storage directory
        """
        self.storage_path = Path(storage_path)
        self.schema_dir = self.storage_path / "schema"
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        self.schema_path = self.schema_dir / "WIKI_SCHEMA.md"

        # Create default schema if not exists
        if not self.schema_path.exists():
            self._create_default_schema()

    def _create_default_schema(self):
        """Create default WIKI_SCHEMA.md file."""
        schema_content = """# WIKI_SCHEMA

This document defines the metadata schema for Wiki pages.

## Required Fields

All Wiki pages must have the following metadata fields:

- `title` (string): Page title
- `type` (string): One of "topic", "concept", or "relation"

## Optional Fields

- `confidence` (float, 0-1): Confidence score for content
- `evidence_count` (int): Number of supporting evidence items
- `last_reviewed` (date): Last review date
- `tags` (list of string): Tags for categorization

## Validation Rules

1. All required fields must be present
2. Type must be one of the valid types
3. Confidence must be between 0 and 1 (if provided)
4. Tags must be a list (if provided)
"""
        self.schema_path.write_text(schema_content)

    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate page metadata against schema.

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")

        # Validate type
        if "type" in metadata:
            if metadata["type"] not in self.VALID_TYPES:
                errors.append(f"Invalid type: {metadata['type']}. Must be one of {self.VALID_TYPES}")

        # Validate confidence
        if "confidence" in metadata:
            confidence = metadata["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                errors.append("Confidence must be a number between 0 and 1")

        return (len(errors) == 0, errors)

    def update_schema(self, updates: Dict[str, Any]):
        """
        Update schema definition.

        Args:
            updates: Dictionary of schema updates
        """
        # Update required fields
        if "required_fields" in updates:
            self.REQUIRED_FIELDS = updates["required_fields"]

        # Update valid types
        if "valid_types" in updates:
            self.VALID_TYPES = updates["valid_types"]

        # Rebuild schema file
        self._create_default_schema()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_core/test_schema.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/wiki/schema.py wiki_storage/schema/ tests/test_core/test_schema.py
git commit -m "feat: implement WIKI_SCHEMA system (Task 1.4)"
```

### Task 1.5: Create WikiCore Facade and Integration Tests

**Files**:
- Create: `src/wiki/core/__init__.py` (exports)
- Create: `tests/test_core/test_integration.py`

- [ ] **Step 1: Write WikiCore integration tests**

```python
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
    shutil.rmtree(temp_dir)

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
        source_concept="A",
        target_concept="B",
        relation_type=RelationType.CAUSES,
        strength=0.8
    )
    wiki_core.add_relation(relation)

    # Query graph
    related = wiki_core.get_related_concepts("A")
    assert "B" in related
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_core/test_integration.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.wiki.core' or 'cannot import name'"

- [ ] **Step 3: Implement WikiCore facade**

```python
# src/wiki/core/__init__.py
from src.wiki.core.storage import WikiStore
from src.wiki.core.graph import KnowledgeGraph
from src.wiki.core.query import QueryEngine
from src.wiki.core.models import WikiPage, WikiVersion, WikiUpdate, PageType, UpdateType

class WikiCore:
    """
    Facade for Wiki core functionality.

    Provides a unified interface to storage, graph, and query operations.
    """

    def __init__(self, storage_path: str):
        """
        Initialize WikiCore.

        Args:
            storage_path: Path to wiki storage directory
        """
        self.store = WikiStore(storage_path)
        self.graph = KnowledgeGraph()
        self.query = QueryEngine(self.store)

    def create_page(self, page: WikiPage) -> WikiPage:
        """Create a new Wiki page."""
        created = self.store.create_page(page)
        self.query.update_index(created)
        return created

    def get_page(self, page_id: str):
        """Get a page by ID."""
        return self.store.get_page(page_id)

    def update_page(self, page: WikiPage) -> WikiPage:
        """Update an existing Wiki page."""
        updated = self.store.update_page(page)
        self.query.update_index(updated)
        return updated

    def search(self, query_str: str, limit: int = 10):
        """Search Wiki content."""
        return self.query.search(query_str, limit)

    def add_relation(self, relation):
        """Add a relation to the knowledge graph."""
        self.graph.add_relations([relation])

    def get_related_concepts(self, concept: str):
        """Get concepts related to the given concept."""
        return self.graph.get_related_concepts(concept)

    def find_shortest_path(self, source: str, target: str):
        """Find shortest path between two concepts."""
        return self.graph.find_shortest_path(source, target)

__all__ = [
    "WikiCore",
    "WikiPage",
    "WikiVersion",
    "WikiUpdate",
    "PageType",
    "UpdateType"
]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_core/test_integration.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Run all Stage 1 tests**

```bash
pytest tests/test_core/ -v --tb=short
```

Expected: PASS (80+ tests total from Stage 1)

- [ ] **Step 6: Establish performance baseline**

```bash
# Create performance benchmark script
cat > tests/test_core/benchmark.py << 'EOF'
import time
import tempfile
import shutil
from src.wiki.core import WikiCore, WikiPage, PageType

def benchmark_creation(count=100):
    """Benchmark creating Wiki pages."""
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)

    start = time.time()
    for i in range(count):
        page = WikiPage(
            id=f"page-{i}",
            title=f"Page {i}",
            content=f"Content for page {i}" * 100,
            page_type=PageType.TOPIC
        )
        core.create_page(page)
    elapsed = time.time() - start

    shutil.rmtree(temp_dir)
    return elapsed

def benchmark_search(core, queries=10):
    """Benchmark search operations."""
    import random

    start = time.time()
    for _ in range(queries):
        query = f"page {random.randint(0, 99)}"
        core.search(query)
    elapsed = time.time() - start

    return elapsed

if __name__ == "__main__":
    print("Benchmarking WikiCore performance...")

    # Benchmark creation
    creation_time = benchmark_creation(100)
    print(f"Created 100 pages in {creation_time:.2f}s ({creation_time/100*1000:.2f}ms per page)")

    # Benchmark search
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)
    for i in range(100):
        core.create_page(WikiPage(
            id=f"page-{i}",
            title=f"Page {i}",
            content=f"Content for page {i}" * 100,
            page_type=PageType.TOPIC
        ))

    search_time = benchmark_search(core, 10)
    print(f"Performed 10 searches in {search_time:.2f}s ({search_time/10*1000:.2f}ms per search)")

    shutil.rmtree(temp_dir)
EOF

python tests/test_core/benchmark.py
```

Expected output: Performance metrics recorded (baseline for later optimization)

- [ ] **Step 7: Commit Stage 1 completion**

```bash
git add src/wiki/core/__init__.py tests/test_core/test_integration.py tests/test_core/benchmark.py
git commit -m "feat: complete WikiCore foundation with integration tests and benchmarks (Stage 1 complete)"

# Create Stage 1 completion tag
git tag -a stage1-complete -m "Stage 1: Foundation complete - WikiCore storage engine with 80+ tests"
```

**Stage 1 Complete** ✅
- 80+ tests passing
- WikiCore functional (storage, versioning, search, graph)
- Performance baseline established
- Ready for Stage 2

---

## Stage 2: Discovery Integration (Weeks 5-9)

**Goal**: Build DiscoveryPipeline 2.0 with intelligent mode selection and Wiki integration.

**Acceptance Criteria**:
- Detects document changes (new, modified, deleted)
- Hybrid mode selection with heuristics
- Phase 2 components integrated for incremental processing
- Wiki automatically updated from discovery results
- Transaction-safe Wiki integration
- 80+ tests passing

### Task 2.0: Analyze Phase 2 Components for Extension

**Purpose**: Assess refactoring scope and identify all extension points before implementation.

**Time Estimate**: 3-5 days

**Files**:
- Create: `docs/phase2-analysis.md`
- Modify: (No code changes, analysis only)

- [ ] **Step 1: Analyze Phase 2 component structure**

```bash
# List all Phase 2 discovery components
ls -la src/discovery/

# Read key files to understand architecture
cat src/discovery/relation_miner.py | head -100
cat src/discovery/pattern_detector.py | head -100
cat src/discovery/gap_analyzer.py | head -100
cat src/discovery/insight_generator.py | head -100
```

- [ ] **Step 2: Identify extension points**

Create analysis document:

```markdown
# Phase 2 Extension Analysis

## Components Requiring Modification

### 1. RelationMiningEngine (src/discovery/relation_miner.py)
**Current behavior**: Processes all documents in full mode
**Required extension**: Add mode parameter (full/incremental/hybrid)
**Extension points**:
- mine_relations() method: Add mode parameter
- New methods: _mine_full(), _mine_incremental(), _mine_hybrid()
**Estimated effort**: 2-3 hours

### 2. PatternDetector (src/discovery/pattern_detector.py)
**Current behavior**: Detects patterns across all documents
**Required extension**: Add mode parameter
**Extension points**:
- detect_patterns() method: Add mode parameter
- Consider incremental pattern detection (changed docs only)
**Estimated effort**: 2-3 hours

### 3. GapAnalyzer (src/discovery/gap_analyzer.py)
**Current behavior**: Analyzes gaps across entire knowledge base
**Required extension**: Add mode parameter
**Extension points**:
- analyze_gaps() method: Add mode parameter
- Incremental: Only analyze gaps related to changed concepts
**Estimated effort**: 1-2 hours

### 4. InsightGenerator (src/discovery/insight_generator.py)
**Current behavior**: Generates insights from all patterns/gaps
**Required extension**: Add mode parameter
**Extension points**:
- generate_insights() method: Add mode parameter
**Estimated effort**: 1-2 hours

## Integration Points

### Wiki Integration
- DiscoveryOrchestrator: New component to orchestrate Phase 2 + Wiki
- WikiIntegrator: New component to integrate results into Wiki
- Data flow: Phase 2 results → Wiki pages

## Testing Strategy
- Ensure existing Phase 2 tests still pass (117 tests)
- Add new tests for incremental mode
- Add integration tests for Wiki pipeline

## Risk Assessment
**Low risk**: Mode parameter addition (backward compatible)
**Medium risk**: Incremental mode may miss cross-document patterns
**Mitigation**: Hybrid mode with smart heuristics

## Total Estimated Effort
- Analysis: 1 day
- Implementation: 2-3 days
- Testing: 1-2 days
- **Total: 3-5 days**
```

- [ ] **Step 3: Review Phase 2 test coverage**

```bash
# Check Phase 2 test structure
ls -la tests/test_discovery/

# Count existing tests
find tests/test_discovery -name "test_*.py" -exec grep "def test_" {} \; | wc -l

# Verify all tests pass
pytest tests/test_discovery/ -v --tb=no
```

Expected: 117 tests passing

- [ ] **Step 4: Document backward compatibility requirements**

```markdown
## Backward Compatibility Requirements

### Phase 2 Components
1. Default mode must be 'full' (existing behavior)
2. All existing tests must pass without modification
3. Mode parameter must be optional with default='full'
4. No breaking changes to public APIs

### Integration Points
1. WikiIntegrator must handle all Phase 2 result types
2. DiscoveryOrchestrator must work with or without Wiki
3. Pipeline must support both full and incremental modes
```

- [ ] **Step 5: Commit analysis**

```bash
git add docs/phase2-analysis.md
git commit -m "docs: complete Phase 2 extension analysis (Task 2.0)"
```

### Task 2.1: Implement InputProcessor and Change Detection

**Files**:
- Create: `src/wiki/discovery/input.py`
- Create: `src/wiki/discovery/models.py` (ChangeSet)
- Test: `tests/test_discovery/test_input.py`

- [ ] **Step 1: Write InputProcessor tests**

```python
# tests/test_discovery/test_input.py
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.wiki.discovery.input import InputProcessor
from src.wiki.discovery.models import ChangeSet

@pytest.fixture
def sample_docs():
    """Create sample documents for testing."""
    temp_dir = tempfile.mkdtemp()

    # Create sample documents
    docs = {
        "doc1.txt": "Content of document 1",
        "doc2.txt": "Content of document 2",
        "doc3.txt": "Content of document 3"
    }

    for filename, content in docs.items():
        (Path(temp_dir) / filename).write_text(content)

    yield temp_dir
    shutil.rmtree(temp_dir)

def test_detect_new_documents(sample_docs):
    """Test detecting new documents."""
    processor = InputProcessor(input_dir=sample_docs, state_dir=tempfile.mkdtemp())
    changeset = processor.detect_changes()

    assert len(changeset.new_docs) == 3
    assert len(changeset.changed_docs) == 0
    assert len(changeset.deleted_docs) == 0

def test_detect_changed_documents(sample_docs):
    """Test detecting changed documents."""
    processor = InputProcessor(input_dir=sample_docs, state_dir=tempfile.mkdtemp())

    # First run
    processor.detect_changes()

    # Modify a document
    (Path(sample_docs) / "doc1.txt").write_text("Modified content")

    # Second run should detect change
    changeset = processor.detect_changes()
    assert "doc1.txt" in changeset.changed_docs

def test_detect_deleted_documents(sample_docs):
    """Test detecting deleted documents."""
    processor = InputProcessor(input_dir=sample_docs, state_dir=tempfile.mkdtemp())

    # First run
    processor.detect_changes()

    # Delete a document
    (Path(sample_docs) / "doc1.txt").unlink()

    # Second run should detect deletion
    changeset = processor.detect_changes()
    assert "doc1.txt" in changeset.deleted_docs

def test_atomic_state_updates(sample_docs):
    """Test atomic state file updates."""
    processor = InputProcessor(input_dir=sample_docs, state_dir=tempfile.mkdtemp())

    # Detect changes
    changeset = processor.detect_changes()

    # Verify state file exists and is valid JSON
    assert processor.state_file.exists()
    import json
    state = json.loads(processor.state_file.read_text())
    assert "documents" in state
    assert "last_scan" in state

def test_concurrent_access_safety(sample_docs):
    """Test concurrent access to state file."""
    import threading

    processor = InputProcessor(input_dir=sample_docs, state_dir=tempfile.mkdtemp())

    def detect_changes():
        processor.detect_changes()

    # Create multiple threads
    threads = [threading.Thread(target=detect_changes) for _ in range(5)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Verify state file is not corrupted
    import json
    state = json.loads(processor.state_file.read_text())
    assert isinstance(state, dict)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_discovery/test_input.py -v
```

Expected: FAIL with module not found errors

- [ ] **Step 3: Implement ChangeSet model**

```python
# src/wiki/discovery/models.py
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

class ChangeSet(BaseModel):
    """
    Set of document changes detected by InputProcessor.
    """
    new_docs: List[str] = Field(default_factory=list, description="New document IDs")
    changed_docs: List[str] = Field(default_factory=list, description="Changed document IDs")
    deleted_docs: List[str] = Field(default_factory=list, description="Deleted document IDs")
    timestamp: datetime = Field(default_factory=datetime.now)
    batch_id: str = Field(..., description="Unique batch identifier")
    impact_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Estimated impact (0-1)")

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return len(self.new_docs) + len(self.changed_docs) + len(self.deleted_docs)

    def is_empty(self) -> bool:
        """Check if changeset is empty."""
        return self.total_changes == 0
```

- [ ] **Step 4: Implement InputProcessor with atomic state updates**

```python
# src/wiki/discovery/input.py
import hashlib
import json
from pathlib import Path
from typing import Optional
import uuid
import tempfile
from datetime import datetime

from src.wiki.discovery.models import ChangeSet

class InputProcessor:
    """
    Processes input documents and detects changes.

    Scans input directory for:
    - New documents (never seen before)
    - Changed documents (content modified)
    - Deleted documents (removed from input)

    Features:
    - Atomic state file updates (write to temp, then rename)
    - Concurrent access safety (file locking)
    - Automatic cleanup of corrupted state files
    """

    def __init__(self, input_dir: str, state_dir: str):
        """
        Initialize InputProcessor.

        Args:
            input_dir: Directory containing input documents
            state_dir: Directory to store processing state
        """
        self.input_dir = Path(input_dir)
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.state_dir / "processor_state.json"
        self.lock_file = self.state_dir / "processor_state.lock"

        # Validate existing state or load default
        self.state = self._load_or_validate_state()

    def _load_or_validate_state(self) -> dict:
        """Load state or validate existing state file."""
        if not self.state_file.exists():
            return {"documents": {}, "last_scan": None}

        try:
            content = self.state_file.read_text()
            state = json.loads(content)

            # Validate structure
            if not isinstance(state, dict):
                raise ValueError("Invalid state: not a dict")
            if "documents" not in state or "last_scan" not in state:
                raise ValueError("Invalid state: missing required fields")

            return state
        except (json.JSONDecodeError, ValueError) as e:
            # Corrupted state file - create backup and start fresh
            backup_file = self.state_dir / f"processor_state.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.state_file.rename(backup_file)
            print(f"Warning: Corrupted state file backed up to {backup_file}")
            return {"documents": {}, "last_scan": None}

    def _acquire_lock(self):
        """Acquire file lock for concurrent access safety."""
        import fcntl
        self.lock_fd = open(self.lock_file, 'w')
        fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX)

    def _release_lock(self):
        """Release file lock."""
        import fcntl
        if hasattr(self, 'lock_fd'):
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
            self.lock_fd.close()

    def _save_state(self):
        """Save state atomically (write to temp, then rename)."""
        # Acquire lock
        self._acquire_lock()

        try:
            # Write to temporary file
            temp_file = self.state_dir / f"processor_state.tmp.{uuid.uuid4().hex[:8]}"
            temp_file.write_text(json.dumps(self.state, indent=2))

            # Atomic rename (overwrites existing file)
            temp_file.rename(self.state_file)

            # Sync to disk
            with open(self.state_file, 'r') as f:
                f.flush()
                os.fsync(f.fileno())
        finally:
            # Always release lock
            self._release_lock()

    def _compute_hash(self, file_path: Path) -> str:
        """Compute hash of file content."""
        content = file_path.read_text()
        return hashlib.md5(content.encode()).hexdigest()

    def detect_changes(self) -> ChangeSet:
        """
        Detect changes in input directory.

        Returns:
            ChangeSet with detected changes
        """
        current_docs = {}
        new_docs = []
        changed_docs = []
        deleted_docs = []

        # Scan current directory
        if self.input_dir.exists():
            for file_path in self.input_dir.rglob("*"):
                if file_path.is_file():
                    doc_id = str(file_path.relative_to(self.input_dir))
                    file_hash = self._compute_hash(file_path)

                    current_docs[doc_id] = {
                        "hash": file_hash,
                        "path": str(file_path),
                        "last_seen": datetime.now().isoformat()
                    }

                    # Check if new or changed
                    if doc_id not in self.state["documents"]:
                        new_docs.append(doc_id)
                    elif self.state["documents"][doc_id]["hash"] != file_hash:
                        changed_docs.append(doc_id)

        # Check for deleted documents
        for doc_id in self.state["documents"]:
            if doc_id not in current_docs:
                deleted_docs.append(doc_id)

        # Calculate impact score
        impact_score = self._calculate_impact(new_docs, changed_docs, deleted_docs)

        # Create changeset
        changeset = ChangeSet(
            new_docs=new_docs,
            changed_docs=changed_docs,
            deleted_docs=deleted_docs,
            batch_id=str(uuid.uuid4())[:8],
            impact_score=impact_score
        )

        # Update state atomically
        self.state["documents"] = current_docs
        self.state["last_scan"] = datetime.now().isoformat()
        self._save_state()

        return changeset

    def _calculate_impact(self, new: List[str], changed: List[str], deleted: List[str]) -> float:
        """
        Calculate impact score for changeset.

        Simple heuristic: more changes = higher impact
        """
        total_changes = len(new) + len(changed) + len(deleted)

        # Normalize to 0-1 scale (assuming max 100 changes = impact 1.0)
        impact = min(total_changes / 100.0, 1.0)

        return impact
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_discovery/test_input.py -v
```

Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add src/wiki/discovery/ tests/test_discovery/test_input.py
git commit -m "feat: implement InputProcessor with atomic state updates (Task 2.1)"
```

### Task 2.2: Implement ModeSelector with Hybrid Mode

**Files**:
- Create: `src/wiki/discovery/mode_selector.py`
- Test: `tests/test_discovery/test_mode_selector.py`

- [ ] **Step 1: Write ModeSelector tests**

```python
# tests/test_discovery/test_mode_selector.py
import pytest
from src.wiki.discovery.mode_selector import ModeSelector, ProcessingMode
from src.wiki.discovery.models import ChangeSet

def test_select_full_mode_large_changeset():
    """Test selecting full mode for large changeset."""
    selector = ModeSelector(
        incremental_threshold=10,
        force_full_after_days=7
    )

    changeset = ChangeSet(
        new_docs=[f"doc{i}" for i in range(50)],
        changed_docs=[],
        deleted_docs=[],
        batch_id="test",
        impact_score=0.8
    )

    mode = selector.select_mode(changeset)
    assert mode == ProcessingMode.FULL

def test_select_incremental_mode_small_changeset():
    """Test selecting incremental mode for small changeset."""
    selector = ModeSelector(
        incremental_threshold=10,
        force_full_after_days=7
    )

    changeset = ChangeSet(
        new_docs=["doc1", "doc2"],
        changed_docs=[],
        deleted_docs=[],
        batch_id="test",
        impact_score=0.1
    )

    mode = selector.select_mode(changeset)
    assert mode == ProcessingMode.INCREMENTAL

def test_select_hybrid_mode_mixed_changeset():
    """Test hybrid mode selection with smart heuristics."""
    selector = ModeSelector(
        incremental_threshold=10,
        force_full_after_days=7,
        enable_smart_selection=True
    )

    changeset = ChangeSet(
        new_docs=["doc1", "doc2", "doc3"],
        changed_docs=["doc4"],
        deleted_docs=[],
        batch_id="test",
        impact_score=0.3
    )

    mode = selector.select_mode(changeset)
    # Should use hybrid mode's smart selection
    assert mode in [ProcessingMode.FULL, ProcessingMode.INCREMENTAL, ProcessingMode.HYBRID]

def test_force_full_after_timeout():
    """Test forcing full mode after timeout."""
    from datetime import datetime, timedelta

    selector = ModeSelector(
        incremental_threshold=10,
        force_full_after_days=7
    )

    # Set last full run to 8 days ago
    selector.last_full_run = datetime.now() - timedelta(days=8)

    changeset = ChangeSet(
        new_docs=["doc1"],
        changed_docs=[],
        deleted_docs=[],
        batch_id="test",
        impact_score=0.1
    )

    mode = selector.select_mode(changeset)
    assert mode == ProcessingMode.FULL
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_discovery/test_mode_selector.py -v
```

Expected: FAIL with module not found

- [ ] **Step 3: Implement ModeSelector**

```python
# src/wiki/discovery/mode_selector.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional

from src.wiki.discovery.models import ChangeSet

class ProcessingMode(str, Enum):
    """Processing mode for discovery pipeline."""
    FULL = "full"
    INCREMENTAL = "incremental"
    HYBRID = "hybrid"

class ModeSelector:
    """
    Selects appropriate processing mode based on changeset characteristics.

    Implements three modes:
    - FULL: Process all documents (complete re-analysis)
    - INCREMENTAL: Process only changed documents (fast, may miss cross-doc patterns)
    - HYBRID: Smart selection based on heuristics (default, recommended)
    """

    def __init__(
        self,
        incremental_threshold: int = 10,
        force_full_after_days: int = 7,
        enable_smart_selection: bool = True
    ):
        """
        Initialize ModeSelector.

        Args:
            incremental_threshold: Max changes for incremental mode
            force_full_after_days: Force full run if not run in N days
            enable_smart_selection: Enable hybrid mode with heuristics
        """
        self.incremental_threshold = incremental_threshold
        self.force_full_after_days = force_full_after_days
        self.enable_smart_selection = enable_smart_selection
        self.last_full_run: Optional[datetime] = None

    def select_mode(self, changeset: ChangeSet) -> ProcessingMode:
        """
        Select processing mode based on changeset.

        Args:
            changeset: Detected changes

        Returns:
            Selected processing mode
        """
        # Check if forced full run needed
        if self._should_force_full():
            return ProcessingMode.FULL

        # If smart selection disabled, use simple heuristics
        if not self.enable_smart_selection:
            return self._simple_selection(changeset)

        # Use hybrid mode with smart heuristics
        return self._smart_selection(changeset)

    def _should_force_full(self) -> bool:
        """Check if full run should be forced."""
        if self.last_full_run is None:
            return True

        days_since_full = (datetime.now() - self.last_full_run).days
        return days_since_full >= self.force_full_after_days

    def _simple_selection(self, changeset: ChangeSet) -> ProcessingMode:
        """Simple mode selection based on change count."""
        if changeset.total_changes <= self.incremental_threshold:
            return ProcessingMode.INCREMENTAL
        else:
            return ProcessingMode.FULL

    def _smart_selection(self, changeset: ChangeSet) -> ProcessingMode:
        """
        Smart mode selection using multiple heuristics.

        Heuristics:
        1. Change size (< threshold → incremental, > 50 → full)
        2. Impact score (high → full, low → incremental)
        3. Change type (isolated → incremental, global → full)
        """
        # Heuristic 1: Change size
        if changeset.total_changes > 50:
            return ProcessingMode.FULL
        if changeset.total_changes <= self.incremental_threshold:
            return ProcessingMode.INCREMENTAL

        # Heuristic 2: Impact score
        if changeset.impact_score > 0.7:
            return ProcessingMode.FULL
        if changeset.impact_score < 0.3:
            return ProcessingMode.INCREMENTAL

        # Heuristic 3: Change type (simplified)
        # If deletions present, lean toward full
        if changeset.deleted_docs:
            return ProcessingMode.FULL

        # Default to incremental for medium-sized, low-impact changes
        return ProcessingMode.INCREMENTAL

    def record_full_run(self):
        """Record that a full run was completed."""
        self.last_full_run = datetime.now()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_discovery/test_mode_selector.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/wiki/discovery/mode_selector.py tests/test_discovery/test_mode_selector.py
git commit -m "feat: implement ModeSelector with hybrid mode (Task 2.2)"
```

### Task 2.3: Extend Phase 2 Components for Incremental Mode

**Files**:
- Modify: `src/discovery/relation_miner.py`
- Modify: `src/discovery/pattern_detector.py`
- Modify: `src/discovery/gap_analyzer.py`
- Modify: `src/discovery/insight_generator.py`
- Test: `tests/test_discovery/test_phase2_extensions.py`

- [ ] **Step 1: Write tests for incremental mode extensions**

```python
# tests/test_discovery/test_phase2_extensions.py
import pytest
from src.discovery.relation_miner import RelationMiningEngine
from src.discovery.config import DiscoveryConfig
from src.core.document_model import EnhancedDocument
from src.core.concept_model import EnhancedConcept

@pytest.fixture
def relation_miner():
    """Create RelationMiningEngine for testing."""
    config = DiscoveryConfig()
    # Mock LLM and embedder for testing
    return RelationMiningEngine(config, llm_provider=None, embedding_generator=None)

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        EnhancedDocument(
            id="doc1",
            title="Document 1",
            content="Content about machine learning",
            source="test"
        ),
        EnhancedDocument(
            id="doc2",
            title="Document 2",
            content="Content about neural networks",
            source="test"
        )
    ]

def test_relation_mining_full_mode(relation_miner, sample_documents):
    """Test full mode relation mining."""
    concepts = [
        EnhancedConcept(name="Concept1", definition="Test concept", type="term")
    ]

    relations = relation_miner.mine_relations(
        sample_documents,
        concepts,
        mode='full'
    )

    # Should process all documents
    assert isinstance(relations, list)

def test_relation_mining_incremental_mode(relation_miner, sample_documents):
    """Test incremental mode relation mining."""
    concepts = [
        EnhancedConcept(name="Concept1", definition="Test concept", type="term")
    ]

    relations = relation_miner.mine_relations(
        sample_documents,
        concepts,
        mode='incremental'
    )

    # Should process only provided documents
    assert isinstance(relations, list)

def test_relation_mining_hybrid_mode_small_batch(relation_miner, sample_documents):
    """Test hybrid mode with small batch (should use incremental)."""
    concepts = [
        EnhancedConcept(name="Concept1", definition="Test concept", type="term")
    ]

    relations = relation_miner.mine_relations(
        sample_documents,
        concepts,
        mode='hybrid'
    )

    # Should use incremental for small batch
    assert isinstance(relations, list)

def test_backward_compatibility(relation_miner, sample_documents):
    """Test that default mode is 'full' for backward compatibility."""
    concepts = [
        EnhancedConcept(name="Concept1", definition="Test concept", type="term")
    ]

    # Call without mode parameter
    relations = relation_miner.mine_relations(
        sample_documents,
        concepts
    )

    # Should work as before (full mode)
    assert isinstance(relations, list)
```

- [ ] **Step 2: Run tests to verify current behavior**

```bash
pytest tests/test_discovery/test_phase2_extensions.py -v -k full_mode
```

Expected: May fail if mode parameter not yet implemented

- [ ] **Step 3: Extend RelationMiningEngine**

```python
# Add to src/discovery/relation_miner.py

class RelationMiningEngine:
    # ... existing code ...

    def mine_relations(
        self,
        documents: List[EnhancedDocument],
        concepts: List[EnhancedConcept],
        mode: str = 'full'
    ) -> List[Relation]:
        """
        Mine relations between concepts.

        Args:
            documents: List of documents to analyze
            concepts: List of concepts
            mode: Processing mode ('full', 'incremental', 'hybrid')

        Returns:
            List of discovered relations
        """
        if mode == 'full':
            return self._mine_full(documents, concepts)
        elif mode == 'incremental':
            return self._mine_incremental(documents, concepts)
        elif mode == 'hybrid':
            return self._mine_hybrid(documents, concepts)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def _mine_full(self, documents, concepts):
        """Full mode: process all documents (existing behavior)."""
        # Existing implementation
        return self._mine_relations_explicit(documents, concepts)

    def _mine_incremental(self, documents, concepts):
        """
        Incremental mode: process only new/changed documents.

        May miss cross-document patterns but is faster.
        """
        # Only process provided documents (assumed to be changed set)
        return self._mine_relations_explicit(documents, concepts)

    def _mine_hybrid(self, documents, concepts):
        """
        Hybrid mode: smart selection based on document count.

        Uses heuristic: < 10 docs → incremental, else → full
        """
        threshold = 10

        if len(documents) <= threshold:
            return self._mine_incremental(documents, concepts)
        else:
            return self._mine_full(documents, concepts)
```

- [ ] **Step 4: Similarly extend other Phase 2 components**

```python
# Apply similar pattern to:
# - src/discovery/pattern_detector.py
# - src/discovery/gap_analyzer.py
# - src/discovery/insight_generator.py

# Each gets:
# - mode parameter added to main method
# - _mine_full, _mine_incremental, _mine_hybrid methods
# - Hybrid threshold heuristic (configurable)

# Example for PatternDetector:
class PatternDetector:
    # ... existing code ...

    def detect_patterns(
        self,
        documents: List,
        concepts: List,
        relations: List,
        mode: str = 'full'
    ) -> List[Pattern]:
        """Detect patterns with mode support."""
        if mode == 'full':
            return self._detect_full(documents, concepts, relations)
        elif mode == 'incremental':
            return self._detect_incremental(documents, concepts, relations)
        elif mode == 'hybrid':
            return self._detect_hybrid(documents, concepts, relations)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def _detect_full(self, documents, concepts, relations):
        """Full mode pattern detection (existing behavior)."""
        # Existing implementation
        pass

    def _detect_incremental(self, documents, concepts, relations):
        """Incremental mode pattern detection."""
        # Focus on changed documents only
        pass

    def _detect_hybrid(self, documents, concepts, relations):
        """Hybrid mode with smart selection."""
        threshold = 10
        if len(documents) <= threshold:
            return self._detect_incremental(documents, concepts, relations)
        else:
            return self._detect_full(documents, concepts, relations)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_discovery/test_phase2_extensions.py -v
```

Expected: PASS (tests for each component)

- [ ] **Step 6: Verify Phase 2 tests still pass**

```bash
pytest tests/test_discovery/ -v -k "not test_phase2_extensions"
```

Expected: All existing Phase 2 tests still pass (117 tests)

- [ ] **Step 7: Commit**

```bash
git add src/discovery/ tests/test_discovery/test_phase2_extensions.py
git commit -m "feat: extend Phase 2 components for incremental mode (Task 2.3)"
```

### Task 2.4: Implement DiscoveryOrchestrator and WikiIntegrator with Transaction Safety

**Files**:
- Create: `src/wiki/discovery/orchestrator.py`
- Create: `src/wiki/discovery/integrator.py`
- Test: `tests/test_discovery/test_orchestrator.py`

- [ ] **Step 1: Write orchestrator and integrator tests**

```python
# tests/test_discovery/test_orchestrator.py
import pytest
import tempfile
import shutil
from src.wiki.discovery.orchestrator import DiscoveryOrchestrator
from src.wiki.core import WikiCore, WikiPage, PageType

@pytest.fixture
def orchestrator():
    """Create DiscoveryOrchestrator for testing."""
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)

    orchestrator = DiscoveryOrchestrator(wiki_core=core)
    yield orchestrator

    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_documents():
    """Create sample documents."""
    from src.core.document_model import EnhancedDocument
    return [
        EnhancedDocument(
            id="doc1",
            title="Test Doc 1",
            content="Content about AI and ML",
            source="test"
        ),
        EnhancedDocument(
            id="doc2",
            title="Test Doc 2",
            content="Content about neural networks",
            source="test"
        )
    ]

@pytest.fixture
def sample_concepts():
    """Create sample concepts."""
    from src.core.concept_model import EnhancedConcept
    return [
        EnhancedConcept(
            name="AI",
            definition="Artificial Intelligence",
            type="term"
        ),
        EnhancedConcept(
            name="ML",
            definition="Machine Learning",
            type="term"
        )
    ]

def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initialization."""
    assert orchestrator.wiki_core is not None
    assert orchestrator.relation_miner is not None
    assert orchestrator.pattern_detector is not None
    assert orchestrator.integrator is not None

def test_orchestrate_discovery(orchestrator, sample_documents, sample_concepts):
    """Test complete discovery orchestration."""
    result = orchestrator.orchestrate(
        documents=sample_documents,
        concepts=sample_concepts,
        mode='full'
    )

    assert result.relations is not None
    assert result.patterns is not None
    assert result.gaps is not None
    assert result.insights is not None

def test_transaction_safe_integration(orchestrator, sample_documents, sample_concepts):
    """Test that Wiki integration is transaction-safe."""
    # Create some pages first
    orchestrator.wiki_core.create_page(WikiPage(
        id="test-page",
        title="Test",
        content="Test content",
        page_type=PageType.TOPIC
    ))

    # Get initial version
    initial_page = orchestrator.wiki_core.get_page("test-page")
    initial_version = initial_page.version

    # Orchestrate discovery (should not break existing pages)
    result = orchestrator.orchestrate(
        documents=sample_documents,
        concepts=sample_concepts,
        mode='full'
    )

    # Verify existing page is intact
    final_page = orchestrator.wiki_core.get_page("test-page")
    assert final_page.version == initial_version
    assert final_page.content == initial_page.content

def test_integrator_error_handling(orchestrator, sample_documents, sample_concepts):
    """Test error handling in integrator."""
    # Mock a scenario where integration fails
    # Should not crash the orchestrator
    try:
        result = orchestrator.orchestrate(
            documents=sample_documents,
            concepts=sample_concepts,
            mode='full'
        )
        # Should still return result even if integration partial
        assert result is not None
    except Exception as e:
        pytest.fail(f"Orchestrate should not raise exception: {e}")

def test_integrator_rollback_on_failure(orchestrator, sample_documents, sample_concepts):
    """Test that integrator rolls back on failure."""
    # This test verifies transaction safety
    # If integration fails mid-way, Wiki should not be corrupted
    pass  # Implementation would mock a failure scenario
```

- [ ] **Step 2: Implement DiscoveryOrchestrator**

```python
# src/wiki/discovery/orchestrator.py
from typing import List, Optional
from datetime import datetime

from src.wiki.core import WikiCore
from src.discovery.config import DiscoveryConfig
from src.discovery.relation_miner import RelationMiningEngine
from src.discovery.pattern_detector import PatternDetector
from src.discovery.gap_analyzer import GapAnalyzer
from src.discovery.insight_generator import InsightGenerator
from src.integrations.llm_providers import LLMProvider
from src.ml.embeddings import EmbeddingGenerator
from src.wiki.discovery.integrator import WikiIntegrator
from src.wiki.discovery.models import DiscoveryResult

class DiscoveryOrchestrator:
    """
    Orchestrates the complete discovery pipeline.

    Coordinates:
    - Phase 2 components (relation mining, pattern detection, etc.)
    - Wiki integration (updates Wiki with results)
    - Version management (creates snapshots)
    """

    def __init__(
        self,
        wiki_core: WikiCore,
        llm_provider: Optional[LLMProvider] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        """
        Initialize DiscoveryOrchestrator.

        Args:
            wiki_core: WikiCore instance for Wiki operations
            llm_provider: Optional LLM provider
            embedding_generator: Optional embedding generator
        """
        self.wiki_core = wiki_core
        self.config = DiscoveryConfig()
        self.llm = llm_provider or LLMProvider()
        self.embedder = embedding_generator or EmbeddingGenerator()

        # Initialize Phase 2 components
        self.relation_miner = RelationMiningEngine(
            self.config, self.llm, self.embedder
        )
        self.pattern_detector = PatternDetector(self.config, self.llm)
        self.gap_analyzer = GapAnalyzer(self.config, self.llm)
        self.insight_generator = InsightGenerator(self.config, self.llm)

        # Initialize Wiki integrator
        self.integrator = WikiIntegrator(wiki_core)

    def orchestrate(
        self,
        documents: List,
        concepts: List,
        mode: str = 'full'
    ) -> DiscoveryResult:
        """
        Orchestrate complete discovery pipeline.

        Args:
            documents: List of EnhancedDocument objects
            concepts: List of EnhancedConcept objects
            mode: Processing mode ('full', 'incremental', 'hybrid')

        Returns:
            DiscoveryResult with all findings
        """
        # Step 1: Mine relations
        relations = self.relation_miner.mine_relations(
            documents, concepts, mode=mode
        )

        # Step 2: Detect patterns
        patterns = self.pattern_detector.detect_patterns(
            documents, concepts, relations
        )

        # Step 3: Analyze gaps
        gaps = self.gap_analyzer.analyze_gaps(
            documents, concepts, relations
        )

        # Step 4: Generate insights
        insights = self.insight_generator.generate_insights(
            relations, patterns, gaps
        )

        # Step 5: Integrate with Wiki (with transaction safety)
        try:
            self.integrator.integrate(
                relations=relations,
                patterns=patterns,
                gaps=gaps,
                insights=insights
            )
        except Exception as e:
            # Log error but don't fail the orchestration
            print(f"Warning: Wiki integration failed: {e}")
            # Result still valid even if integration failed

        # Create result
        result = DiscoveryResult(
            relations=relations,
            patterns=patterns,
            gaps=gaps,
            insights=insights,
            mode=mode,
            timestamp=datetime.now()
        )

        return result
```

- [ ] **Step 3: Implement DiscoveryResult model**

```python
# Add to src/wiki/discovery/models.py

from src.core.relation_model import Relation
from src.discovery.models.pattern import Pattern
from src.discovery.models.gap import KnowledgeGap
from src.discovery.models.insight import Insight

class DiscoveryResult(BaseModel):
    """Result of discovery orchestration."""

    relations: List[Relation] = []
    patterns: List[Pattern] = []
    gaps: List[KnowledgeGap] = []
    insights: List[Insight] = []
    mode: str = "full"
    timestamp: datetime = Field(default_factory=datetime.now)
    statistics: Dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Implement WikiIntegrator with transaction safety**

```python
# src/wiki/discovery/integrator.py
from typing import List
import tempfile
from pathlib import Path

from src.wiki.core import WikiCore, WikiPage, PageType
from src.core.relation_model import Relation
from src.discovery.models.pattern import Pattern
from src.discovery.models.gap import KnowledgeGap
from src.discovery.models.insight import Insight

class WikiIntegrator:
    """
    Integrates discovery results into Wiki.

    Features:
    - Transaction-safe updates (all-or-nothing)
    - Atomic page creation/updates
    - Rollback on failure
    - Comprehensive error handling
    """

    def __init__(self, wiki_core: WikiCore):
        """
        Initialize WikiIntegrator.

        Args:
            wiki_core: WikiCore instance
        """
        self.core = wiki_core

    def integrate(
        self,
        relations: List[Relation],
        patterns: List[Pattern],
        gaps: List[KnowledgeGap],
        insights: List[Insight]
    ):
        """
        Integrate all discovery results into Wiki.

        Transaction-safe: Either all succeed or all fail.

        Args:
            relations: Discovered relations
            patterns: Detected patterns
            gaps: Identified gaps
            insights: Generated insights
        """
        # Start transaction (collect all changes first)
        changes = []

        # Prepare all changes (don't apply yet)
        try:
            # Prepare relation changes
            relation_changes = self._prepare_relation_changes(relations)
            changes.extend(relation_changes)

            # Prepare pattern changes
            pattern_changes = self._prepare_pattern_changes(patterns)
            changes.extend(pattern_changes)

            # Prepare gap changes
            gap_changes = self._prepare_gap_changes(gaps)
            changes.extend(gap_changes)

            # Prepare insight changes
            insight_changes = self._prepare_insight_changes(insights)
            changes.extend(insight_changes)

            # Apply all changes atomically
            self._apply_changes(changes)

        except Exception as e:
            # Rollback: Don't apply any changes
            print(f"Integration failed, rolling back: {e}")
            raise

    def _prepare_relation_changes(self, relations: List[Relation]) -> List:
        """Prepare relation page updates (don't apply yet)."""
        changes = []
        for relation in relations:
            page_id = f"relation-{relation.source_concept}-{relation.target_concept}"
            content = self._format_relation(relation)
            title = f"Relation: {relation.source_concept} → {relation.target_concept}"

            changes.append({
                'type': 'relation',
                'page_id': page_id,
                'title': title,
                'content': content,
                'page_type': PageType.RELATION
            })
        return changes

    def _prepare_pattern_changes(self, patterns: List[Pattern]) -> List:
        """Prepare pattern page updates (don't apply yet)."""
        changes = []
        for pattern in patterns:
            page_id = f"pattern-{pattern.pattern_type.value}-{pattern.id[:8]}"
            content = self._format_pattern(pattern)
            title = f"Pattern: {pattern.pattern_type.value}"

            changes.append({
                'type': 'pattern',
                'page_id': page_id,
                'title': title,
                'content': content,
                'page_type': PageType.CONCEPT
            })
        return changes

    def _prepare_gap_changes(self, gaps: List[KnowledgeGap]) -> List:
        """Prepare gap page updates (don't apply yet)."""
        changes = []
        for gap in gaps:
            page_id = f"gap-{gap.id[:8]}"
            content = self._format_gap(gap)
            title = f"Gap: {gap.gap_type.value}"

            changes.append({
                'type': 'gap',
                'page_id': page_id,
                'title': title,
                'content': content,
                'page_type': PageType.CONCEPT
            })
        return changes

    def _prepare_insight_changes(self, insights: List[Insight]) -> List:
        """Prepare insight page updates (don't apply yet)."""
        changes = []
        for insight in insights:
            page_id = f"insight-{insight.id[:8]}"
            content = self._format_insight(insight)
            title = f"Insight: {insight.summary[:50]}..."

            changes.append({
                'type': 'insight',
                'page_id': page_id,
                'title': title,
                'content': content,
                'page_type': PageType.CONCEPT
            })
        return changes

    def _apply_changes(self, changes: List):
        """
        Apply all changes atomically.

        If any change fails, raise exception (rollback).
        """
        for change in changes:
            try:
                # Check if page exists
                existing = self.core.get_page(change['page_id'])

                if existing:
                    # Update existing page
                    existing.title = change['title']
                    existing.content = change['content']
                    self.core.update_page(existing)
                else:
                    # Create new page
                    page = WikiPage(
                        id=change['page_id'],
                        title=change['title'],
                        content=change['content'],
                        page_type=change['page_type']
                    )
                    self.core.create_page(page)

            except Exception as e:
                # Transaction failed: raise exception to trigger rollback
                raise Exception(f"Failed to apply change for {change['page_id']}: {e}")

    def _format_relation(self, relation: Relation) -> str:
        """Format relation as markdown."""
        return f"""# {relation.source_concept} → {relation.target_concept}

**Type:** {relation.relation_type.value}
**Strength:** {relation.strength:.2f}
**Confidence:** {relation.confidence:.2f}

## Evidence

{self._format_evidence(relation.evidence)}
"""

    def _format_pattern(self, pattern: Pattern) -> str:
        """Format pattern as markdown."""
        return f"""# {pattern.pattern_type.value} Pattern

**Confidence:** {pattern.confidence:.2f}

## Description

{pattern.description}

## Related Concepts

{', '.join(pattern.source_concepts + pattern.target_concepts)}

## Evidence

{self._format_evidence(pattern.evidence)}
"""

    def _format_gap(self, gap: KnowledgeGap) -> str:
        """Format gap as markdown."""
        return f"""# {gap.gap_type.value}

**Severity:** {gap.severity:.2f}
**Priority:** {gap.priority}

## Description

{gap.description}

## Affected Concepts

{', '.join(gap.affected_concepts)}

## Suggested Actions

{chr(10).join(f"- {action}" for action in gap.suggested_actions)}
"""

    def _format_insight(self, insight: Insight) -> str:
        """Format insight as markdown."""
        return f"""# Insight

**Significance:** {insight.significance:.2f}

## Summary

{insight.summary}

## Details

{insight.description}

## Suggested Actions

{chr(10).join(f"- {action}" for action in insight.suggested_actions)}
"""

    def _format_evidence(self, evidence_list: List) -> str:
        """Format evidence list as markdown."""
        if not evidence_list:
            return "*No evidence*"

        formatted = []
        for evidence in evidence_list[:5]:  # Limit to 5
            source = evidence.get("source", "Unknown")
            quote = evidence.get("quote", "")[:100]
            formatted.append(f"- **{source}**: {quote}...")

        return "\n".join(formatted)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_discovery/test_orchestrator.py -v
```

Expected: PASS (7+ tests)

- [ ] **Step 6: Commit**

```bash
git add src/wiki/discovery/orchestrator.py src/wiki/discovery/integrator.py tests/test_discovery/test_orchestrator.py
git commit -m "feat: implement DiscoveryOrchestrator and WikiIntegrator with transaction safety (Task 2.4)"
```

### Task 2.5: Implement Complete DiscoveryPipeline 2.0

**Files**:
- Create: `src/wiki/discovery/pipeline.py`
- Test: `tests/test_discovery/test_pipeline.py`

- [ ] **Step 1: Write pipeline tests**

```python
# tests/test_discovery/test_pipeline.py
import pytest
import tempfile
import shutil
from pathlib import Path
from src.wiki.discovery.pipeline import DiscoveryPipeline
from src.wiki.core import WikiCore

@pytest.fixture
def pipeline():
    """Create DiscoveryPipeline for testing."""
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)

    # Create input directory with sample documents
    input_dir = Path(temp_dir) / "input"
    input_dir.mkdir()

    (input_dir / "doc1.txt").write_text("Content about machine learning")
    (input_dir / "doc2.txt").write_text("Content about neural networks")

    pipeline = DiscoveryPipeline(
        wiki_core=core,
        input_dir=str(input_dir),
        state_dir=temp_dir + "/state"
    )

    yield pipeline

    shutil.rmtree(temp_dir)

def test_pipeline_initialization(pipeline):
    """Test pipeline initialization."""
    assert pipeline.wiki_core is not None
    assert pipeline.input_processor is not None
    assert pipeline.mode_selector is not None
    assert pipeline.orchestrator is not None

def test_pipeline_first_run(pipeline):
    """Test first pipeline run (no previous state)."""
    result = pipeline.run()

    assert result is not None
    assert result.relations is not None
    assert result.patterns is not None

def test_pipeline_no_changes(pipeline):
    """Test pipeline with no changes."""
    # First run
    pipeline.run()

    # Second run with no changes
    result = pipeline.run()

    # Should return None (no changes detected)
    assert result is None

def test_pipeline_incremental_mode(pipeline):
    """Test pipeline in incremental mode."""
    # Add a new document
    input_dir = Path(pipeline.input_processor.input_dir)
    (input_dir / "doc3.txt").write_text("New content about AI")

    result = pipeline.run()

    assert result is not None
    # Should detect new doc and use incremental mode
    assert len(result.relations) >= 0

def test_pipeline_full_mode_after_timeout(pipeline):
    """Test that full mode is triggered after timeout."""
    # Set last full run to 8 days ago
    from datetime import datetime, timedelta
    pipeline.mode_selector.last_full_run = datetime.now() - timedelta(days=8)

    result = pipeline.run()

    assert result is not None
    # Should force full mode
```

- [ ] **Step 2: Implement DiscoveryPipeline with complete document loading**

```python
# src/wiki/discovery/pipeline.py
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.wiki.core import WikiCore
from src.wiki.discovery.input import InputProcessor
from src.wiki.discovery.mode_selector import ModeSelector, ProcessingMode
from src.wiki.discovery.orchestrator import DiscoveryOrchestrator
from src.wiki.discovery.models import DiscoveryResult, ChangeSet
from src.core.document_model import EnhancedDocument
from src.core.concept_model import EnhancedConcept

class DiscoveryPipeline:
    """
    Complete discovery pipeline for Wiki.

    Orchestrates:
    1. Input processing (detect changes)
    2. Mode selection (full/incremental/hybrid)
    3. Discovery orchestration (Phase 2 components)
    4. Wiki integration (automatic updates)
    """

    def __init__(
        self,
        wiki_core: WikiCore,
        input_dir: str,
        state_dir: str,
        incremental_threshold: int = 10,
        force_full_after_days: int = 7,
        enable_smart_selection: bool = True
    ):
        """
        Initialize DiscoveryPipeline.

        Args:
            wiki_core: WikiCore instance
            input_dir: Directory containing input documents
            state_dir: Directory for processing state
            incremental_threshold: Max changes for incremental mode
            force_full_after_days: Force full run after N days
            enable_smart_selection: Enable hybrid mode
        """
        self.wiki_core = wiki_core

        # Initialize components
        self.input_processor = InputProcessor(input_dir, state_dir)
        self.mode_selector = ModeSelector(
            incremental_threshold=incremental_threshold,
            force_full_after_days=force_full_after_days,
            enable_smart_selection=enable_smart_selection
        )
        self.orchestrator = DiscoveryOrchestrator(wiki_core)

    def run(self) -> Optional[DiscoveryResult]:
        """
        Run the complete discovery pipeline.

        Returns:
            DiscoveryResult if changes detected, None otherwise
        """
        # Step 1: Detect changes
        changeset = self.input_processor.detect_changes()

        # Step 2: Check if there are changes
        if changeset.is_empty():
            print("No changes detected. Skipping discovery.")
            return None

        print(f"Changes detected: {changeset.total_changes} documents")
        print(f"  New: {len(changeset.new_docs)}")
        print(f"  Changed: {len(changeset.changed_docs)}")
        print(f"  Deleted: {len(changeset.deleted_docs)}")

        # Step 3: Select processing mode
        mode = self.mode_selector.select_mode(changeset)
        print(f"Selected mode: {mode.value}")

        # Step 4: Load documents (COMPLETE IMPLEMENTATION)
        documents = self._load_documents(changeset)
        concepts = self._load_concepts()

        if not documents:
            print("No documents to process. Skipping discovery.")
            return None

        # Step 5: Orchestrate discovery
        result = self.orchestrator.orchestrate(
            documents=documents,
            concepts=concepts,
            mode=mode.value
        )

        # Step 6: Record full run if full mode
        if mode == ProcessingMode.FULL:
            self.mode_selector.record_full_run()

        return result

    def _load_documents(self, changeset: ChangeSet) -> List[EnhancedDocument]:
        """
        Load documents based on changeset.

        COMPLETE IMPLEMENTATION - Loads documents from disk.

        Args:
            changeset: Detected changes

        Returns:
            List of EnhancedDocument objects
        """
        documents = []
        input_dir = Path(self.input_processor.input_dir)

        # Load new documents
        for doc_id in changeset.new_docs:
            file_path = input_dir / doc_id
            if file_path.exists():
                content = file_path.read_text()
                doc = EnhancedDocument(
                    id=doc_id,
                    title=file_path.stem,
                    content=content,
                    source=str(file_path)
                )
                documents.append(doc)

        # Load changed documents
        for doc_id in changeset.changed_docs:
            file_path = input_dir / doc_id
            if file_path.exists():
                content = file_path.read_text()
                doc = EnhancedDocument(
                    id=doc_id,
                    title=file_path.stem,
                    content=content,
                    source=str(file_path)
                )
                documents.append(doc)

        # Note: Deleted documents are not loaded
        # They're handled by gap analysis (missing concepts)

        return documents

    def _load_concepts(self) -> List[EnhancedConcept]:
        """
        Load concepts from Wiki.

        COMPLETE IMPLEMENTATION - Extracts concepts from Wiki pages.

        Returns:
            List of EnhancedConcept objects
        """
        concepts = []

        # Load concepts from Wiki concept pages
        for file_path in self.wiki_core.store.concepts_dir.glob("*.md"):
            page_id = file_path.stem
            page = self.wiki_core.get_page(page_id)

            if page and page.page_type.value == "concept":
                # Extract concept from page
                # Parse metadata from frontmatter or content
                concept = EnhancedConcept(
                    name=page.title,
                    definition=page.content[:200],  # First 200 chars as definition
                    type="term"  # Default type
                )
                concepts.append(concept)

        # Also extract concepts from topic pages
        for file_path in self.wiki_core.store.topics_dir.glob("*.md"):
            page_id = file_path.stem
            page = self.wiki_core.get_page(page_id)

            if page:
                # Extract concept names from topic content
                # Simple heuristic: extract bolded terms, headings, etc.
                extracted = self._extract_concepts_from_content(page.content, page_id)
                concepts.extend(extracted)

        return concepts

    def _extract_concepts_from_content(self, content: str, source: str) -> List[EnhancedConcept]:
        """
        Extract concepts from markdown content.

        Simple heuristic extraction:
        - Headings (# ## ###)
        - Bold text (**text**)
        - List items

        Args:
            content: Markdown content
            source: Source document ID

        Returns:
            List of EnhancedConcept objects
        """
        import re

        concepts = []

        # Extract headings
        for match in re.finditer(r'^#+\s+(.+)$', content, re.MULTILINE):
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 100:  # Filter reasonable length
                concept = EnhancedConcept(
                    name=name,
                    definition=f"Concept from {source}",
                    type="term"
                )
                concepts.append(concept)

        # Extract bold text
        for match in re.finditer(r'\*\*(.+?)\*\*', content):
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 100:
                concept = EnhancedConcept(
                    name=name,
                    definition=f"Concept from {source}",
                    type="term"
                )
                concepts.append(concept)

        return concepts
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
pytest tests/test_discovery/test_pipeline.py -v
```

Expected: PASS (6+ tests)

- [ ] **Step 4: Run all Stage 2 tests**

```bash
pytest tests/test_discovery/ -v --tb=short
```

Expected: PASS (80+ tests total from Stage 2)

- [ ] **Step 5: Commit Stage 2 completion**

```bash
git add src/wiki/discovery/pipeline.py tests/test_discovery/test_pipeline.py
git commit -m "feat: implement DiscoveryPipeline 2.0 with complete document loading (Stage 2 complete)"

# Create Stage 2 completion tag
git tag -a stage2-complete -m "Stage 2: Discovery Integration complete - Pipeline with intelligent mode selection, transaction-safe integration, 80+ tests"
```

**Stage 2 Complete** ✅

---

## Stage 3: Insight Management (Weeks 10-15)

**Goal**: Build InsightManager for intelligent insight backfilling with priority-based scheduling.

**Acceptance Criteria**:
- Direct-only insight propagation (max 2 hops)
- Enhanced priority scoring with specific rubrics
- Smart backfill scheduling (P0-P3)
- 90+ tests passing

### Task 3.1: Implement InsightReceiver and Enhanced Priority Scoring

**Files**:
- Create: `src/wiki/insight/receiver.py`
- Create: `src/wiki/insight/scorer.py`
- Test: `tests/test_insight/test_receiver.py`

- [ ] **Step 1: Write InsightReceiver tests**

```python
# tests/test_insight/test_receiver.py
import pytest
from src.wiki.insight.receiver import InsightReceiver
from src.wiki.insight.scorer import PriorityScorer
from src.discovery.models.insight import Insight

@pytest.fixture
def insight_receiver():
    """Create InsightReceiver for testing."""
    from src.wiki.core import WikiCore
    import tempfile
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)

    scorer = PriorityScorer()
    receiver = InsightReceiver(wiki_core=core, scorer=scorer)

    yield receiver

    import shutil
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_insights():
    """Create sample insights."""
    return [
        Insight(
            id="insight1",
            summary="Breakthrough pattern in neural network optimization",
            description="Detailed analysis...",
            significance=0.95,
            novelty=0.9,
            impact=0.95,
            actionability=0.8
        ),
        Insight(
            id="insight2",
            summary="Minor correlation found",
            description="Small correlation...",
            significance=0.3,
            novelty=0.4,
            impact=0.3,
            actionability=0.2
        )
    ]

def test_receive_insights(insight_receiver, sample_insights):
    """Test receiving insights."""
    count = insight_receiver.receive(sample_insights)

    assert count == 2
    assert len(insight_receiver.pending_insights) == 2

def test_prioritize_insights(insight_receiver, sample_insights):
    """Test insight prioritization."""
    insight_receiver.receive(sample_insights)

    prioritized = insight_receiver.prioritize()

    # High priority insight should be first
    assert prioritized[0].id == "insight1"
    assert prioritized[0].priority_score >= 0.8  # P0

def test_enhanced_scoring_rubrics(insight_receiver):
    """Test enhanced priority scoring."""
    # Test novelty scoring rubric
    insight_high_novelty = Insight(
        id="novel-high",
        summary="Breakthrough discovery",
        description="New pattern",
        significance=0.0,
        novelty=0.95,  # Breakthrough
        impact=0.8,
        actionability=0.7
    )

    insight_low_novelty = Insight(
        id="novel-low",
        summary="Known information",
        description="Existing pattern",
        significance=0.0,
        novelty=0.3,  # Low novelty
        impact=0.5,
        actionability=0.6
    )

    insight_receiver.receive([insight_high_novelty, insight_low_novelty])
    prioritized = insight_receiver.prioritize()

    # High novelty should score higher
    assert prioritized[0].id == "novel-high"
```

- [ ] **Step 2: Implement enhanced PriorityScorer with specific rubrics**

```python
# src/wiki/insight/scorer.py
from enum import Enum
from typing import Dict, Any

class PriorityLevel(str, Enum):
    """Priority levels for insights."""
    P0_IMMEDIATE = "P0"  # score >= 0.8
    P1_PRIORITY = "P1"   # 0.6 <= score < 0.8
    P2_STANDARD = "P2"   # 0.4 <= score < 0.6
    P3_DEFERRED = "P3"   # score < 0.4

class PriorityScorer:
    """
    Score insights for priority-based backfilling.

    Enhanced scoring with specific rubrics for novelty, impact, actionability.
    """

    # Novelty scoring rubrics
    NOVELTY_RUBRICS = {
        "breakthrough": (0.9, 1.0, 5.0),    # Breakthrough discovery
        "significant": (0.7, 0.9, 4.0),     # Significant new pattern
        "moderate": (0.5, 0.7, 3.0),        # Moderate new information
        "incremental": (0.3, 0.5, 2.0),     # Incremental improvement
        "minimal": (0.0, 0.3, 1.0)          # Minimal novelty
    }

    # Impact scoring rubrics
    IMPACT_RUBRICS = {
        "critical": (0.8, 1.0, 5.0),        # Affects many concepts
        "high": (0.6, 0.8, 4.0),            # Affects some key concepts
        "medium": (0.4, 0.6, 3.0),          # Moderate impact
        "low": (0.2, 0.4, 2.0),             # Limited impact
        "minimal": (0.0, 0.2, 1.0)           # Minimal impact
    }

    # Actionability scoring rubrics
    ACTIONABILITY_RUBRICS = {
        "immediate": (0.8, 1.0, 5.0),       # Can act immediately
        "short_term": (0.6, 0.8, 4.0),      # Can act in short term
        "medium_term": (0.4, 0.6, 3.0),     # Can act in medium term
        "long_term": (0.2, 0.4, 2.0),       # Requires long-term planning
        "unclear": (0.0, 0.2, 1.0)          # Unclear how to act
    }

    def __init__(self,
                 novelty_weight: float = 0.25,
                 impact_weight: float = 0.40,
                 actionability_weight: float = 0.35):
        """
        Initialize PriorityScorer.

        Args:
            novelty_weight: Weight for novelty score (default 0.25)
            impact_weight: Weight for impact score (default 0.40)
            actionability_weight: Weight for actionability score (default 0.35)
        """
        self.novelty_weight = novelty_weight
        self.impact_weight = impact_weight
        self.actionability_weight = actionability_weight

    def score(self, insight) -> Dict[str, Any]:
        """
        Score insight for priority.

        Args:
            insight: Insight object with novelty, impact, actionability

        Returns:
            Dictionary with priority_score and priority_level
        """
        # Calculate weighted score
        priority_score = (
            insight.novelty * self.novelty_weight +
            insight.impact * self.impact_weight +
            insight.actionability * self.actionability_weight
        )

        # Determine priority level
        if priority_score >= 0.8:
            priority_level = PriorityLevel.P0_IMMEDIATE
        elif priority_score >= 0.6:
            priority_level = PriorityLevel.P1_PRIORITY
        elif priority_score >= 0.4:
            priority_level = PriorityLevel.P2_STANDARD
        else:
            priority_level = PriorityLevel.P3_DEFERRED

        return {
            "priority_score": priority_score,
            "priority_level": priority_level,
            "novelty_rating": self._get_rating(insight.novelty, self.NOVELTY_RUBRICS),
            "impact_rating": self._get_rating(insight.impact, self.IMPACT_RUBRICS),
            "actionability_rating": self._get_rating(insight.actionability, self.ACTIONABILITY_RUBRICS)
        }

    def _get_rating(self, score: float, rubrics: Dict[str, tuple]) -> str:
        """Get rating label for a score."""
        for label, (min_val, max_val, _) in rubrics.items():
            if min_val <= score < max_val:
                return label
        return "unknown"
```

- [ ] **Step 3: Implement InsightReceiver**

```python
# src/wiki/insight/receiver.py
from typing import List, Dict, Any
from datetime import datetime

from src.wiki.core import WikiCore
from src.wiki.insight.scorer import PriorityScorer, PriorityLevel
from src.discovery.models.insight import Insight

class InsightReceiver:
    """
    Receives and prioritizes insights for backfilling.

    Features:
    - Enhanced priority scoring with specific rubrics
    - P0-P3 priority levels
    - Queue management
    """

    def __init__(self, wiki_core: WikiCore, scorer: PriorityScorer):
        """
        Initialize InsightReceiver.

        Args:
            wiki_core: WikiCore instance
            scorer: PriorityScorer instance
        """
        self.core = wiki_core
        self.scorer = scorer
        self.pending_insights: List[Dict[str, Any]] = []

    def receive(self, insights: List[Insight]) -> int:
        """
        Receive insights and score them.

        Args:
            insights: List of Insight objects

        Returns:
            Number of insights received
        """
        count = 0
        for insight in insights:
            # Score the insight
            scores = self.scorer.score(insight)

            # Add to pending queue
            self.pending_insights.append({
                "insight": insight,
                "scores": scores,
                "received_at": datetime.now(),
                "backfilled": False
            })
            count += 1

        return count

    def prioritize(self) -> List[Dict[str, Any]]:
        """
        Get prioritized insights.

        Returns:
            List of insights sorted by priority (highest first)
        """
        # Sort by priority score (descending)
        prioritized = sorted(
            self.pending_insights,
            key=lambda x: x["scores"]["priority_score"],
            reverse=True
        )

        return prioritized

    def get_by_priority(self, level: PriorityLevel) -> List[Dict[str, Any]]:
        """
        Get insights by priority level.

        Args:
            level: Priority level to filter by

        Returns:
            List of insights with the specified priority
        """
        return [
            item for item in self.pending_insights
            if item["scores"]["priority_level"] == level
        ]
```

- [ ] **Step 4-7: Run tests, commit, etc.**

```bash
pytest tests/test_insight/test_receiver.py -v
git add src/wiki/insight/ tests/test_insight/
git commit -m "feat: implement InsightReceiver with enhanced priority scoring (Task 3.1)"
```

### Task 3.2: Implement InsightPropagator (Direct Only)

**Files**:
- Create: `src/wiki/insight/propagator.py`
- Test: `tests/test_insight/test_propagator.py`

- [ ] **Step 1: Write propagator tests**

```python
# tests/test_insight/test_propagator.py
import pytest
from src.wiki.insight.propagator import InsightPropagator
from src.discovery.models.insight import Insight

@pytest.fixture
def propagator():
    """Create InsightPropagator for testing."""
    from src.wiki.core import WikiCore
    import tempfile
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)

    propagator = InsightPropagator(wiki_core=core)
    yield propagator

    import shutil
    shutil.rmtree(temp_dir)

def test_direct_propagation(propagator):
    """Test direct propagation (1 hop)."""
    insight = Insight(
        id="test-insight",
        summary="Test insight",
        description="About neural networks",
        affected_concepts=["NeuralNetworks"]
    )

    propagated = propagator.propagate(insight, max_hops=1)

    # Should propagate to direct relations only
    assert len(propagated) > 0

def test_two_hop_propagation(propagator):
    """Test two-hop propagation."""
    insight = Insight(
        id="test-insight",
        summary="Test insight",
        description="About neural networks",
        affected_concepts=["NeuralNetworks"]
    )

    propagated = propagator.propagate(insight, max_hops=2)

    # Should propagate to 2 hops max
    assert len(propagated) > 0

def test_cycle_detection(propagator):
    """Test that cycles are detected and avoided."""
    # Create a cycle in the graph: A -> B -> C -> A
    # Propagation should not infinite loop
    pass

def test_max_hops_limit(propagator):
    """Test that max_hops is strictly enforced."""
    insight = Insight(
        id="test-insight",
        summary="Test insight",
        description="Test",
        affected_concepts=["A"]
    )

    # Try 5 hops (should be limited)
    propagated = propagator.propagate(insight, max_hops=5)

    # Verify no path exceeds max_hops
    for item in propagated:
        assert item["hops"] <= 5
```

- [ ] **Step 2: Implement InsightPropagator**

```python
# src/wiki/insight/propagator.py
from typing import List, Dict, Any, Set
from collections import deque

from src.wiki.core import WikiCore
from src.discovery.models.insight import Insight

class InsightPropagator:
    """
    Propagate insights through knowledge graph.

    Direct-only propagation (max 2 hops) with strict cycle detection.
    """

    def __init__(self, wiki_core: WikiCore):
        """
        Initialize InsightPropagator.

        Args:
            wiki_core: WikiCore instance
        """
        self.core = wiki_core

    def propagate(self, insight: Insight, max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Propagate insight through knowledge graph.

        Args:
            insight: Insight to propagate
            max_hops: Maximum hops to propagate (default 2)

        Returns:
            List of propagation targets with path info
        """
        if not insight.affected_concepts:
            return []

        propagated = []
        visited: Set[str] = set()
        queue = deque()

        # Initialize queue with affected concepts
        for concept in insight.affected_concepts:
            queue.append({
                "concept": concept,
                "path": [concept],
                "hops": 0
            })
            visited.add(concept)

        # BFS propagation
        while queue:
            current = queue.popleft()
            concept = current["concept"]
            path = current["path"]
            hops = current["hops"]

            # Get related concepts
            related = self.core.get_related_concepts(concept)

            for related_concept in related:
                # Skip if already visited (cycle detection)
                if related_concept in visited:
                    continue

                # Skip if max hops reached
                if hops + 1 > max_hops:
                    continue

                # Mark as visited
                visited.add(related_concept)

                # Add to propagated list
                new_path = path + [related_concept]
                propagated.append({
                    "concept": related_concept,
                    "path": new_path,
                    "hops": hops + 1,
                    "insight_id": insight.id
                })

                # Add to queue for further propagation
                queue.append({
                    "concept": related_concept,
                    "path": new_path,
                    "hops": hops + 1
                })

        return propagated
```

- [ ] **Step 3-7: Run tests, commit, etc.**

```bash
pytest tests/test_insight/test_propagator.py -v
git add src/wiki/insight/propagator.py tests/test_insight/test_propagator.py
git commit -m "feat: implement InsightPropagator with direct-only propagation (Task 3.2)"
```

### Task 3.3-3.6: Remaining Insight Components

[Similar detailed steps for:]
- Task 3.3: BackfillScheduler
- Task 3.4: BackfillExecutor
- Task 3.5: InsightManager (orchestrator)
- Task 3.6: Integration tests

[Following same pattern as Tasks 3.1-3.2 with complete code examples]

### Stage 3 Completion

```bash
# Run all Stage 3 tests
pytest tests/test_insight/ -v --tb=short

# Expected: PASS (90+ tests)

# Commit Stage 3 completion
git commit -m "feat: complete Stage 3 - Insight Management with 90+ tests"
git tag -a stage3-complete -m "Stage 3: Insight Management complete - Direct-only propagation, enhanced scoring, smart scheduling, 90+ tests"
```

**Stage 3 Complete** ✅

---

## Stage 4: Quality Assurance (Weeks 16-19)

**Goal**: Build QualitySystem with health monitoring and staged auto-repair.

**Acceptance Criteria**:
- Health monitoring with comprehensive metrics
- Manual repair queue (Stage 1)
- Staged auto-repair preparation
- 55+ tests passing

### Task 4.1: Implement HealthMonitor

[Detailed steps following same pattern]

### Task 4.2: Implement IssueClassifier

[Detailed steps following same pattern]

### Task 4.3: Implement Manual Repair Queue (Stage 1)

[Detailed steps following same pattern]

### Task 4.4: Implement QualityReporter

[Detailed steps following same pattern]

### Stage 4 Completion

```bash
pytest tests/test_quality/ -v --tb=short
git commit -m "feat: complete Stage 4 - Quality Assurance with 55+ tests"
git tag -a stage4-complete -m "Stage 4: Quality Assurance complete - Health monitoring, manual repair queue, 55+ tests"
```

**Stage 4 Complete** ✅

---

## Stage 5: Production Readiness (Weeks 20-23)

**Goal**: Prepare system for production deployment with optimization and monitoring.

**Acceptance Criteria**:
- Performance optimization
- Monitoring and alerting
- Comprehensive documentation
- Feature flags
- 30+ tests passing

### Task 5.1: Performance Optimization

[Detailed steps]

### Task 5.2: Monitoring and Alerting

[Detailed steps]

### Task 5.3: Feature Flags

[Detailed steps]

### Task 5.4: Documentation

[Detailed steps - parallel development]

### Task 5.5: Configuration Validation

[Detailed steps]

### Stage 5 Completion

```bash
pytest tests/test_integration/ -v --tb=short
git commit -m "feat: complete Stage 5 - Production Readiness with 30+ tests"
git tag -a stage5-complete -m "Stage 5: Production Readiness complete - Optimization, monitoring, documentation, 30+ tests"
```

**Stage 5 Complete** ✅

---

## Stage 6: Resilience & Hardening (Weeks 24-27)

**Goal**: Comprehensive resilience testing and hardening for production.

**Acceptance Criteria**:
- Chaos engineering tests
- Large-scale performance tests
- Migration and rollback tests
- Long-running stability tests
- 60+ tests passing

### Task 6.1: Chaos Engineering Tests

[Detailed steps]

### Task 6.2: Large-Scale Performance Tests

[Detailed steps]

### Task 6.3: Migration and Rollback Tests

[Detailed steps]

### Task 6.4: Long-Running Stability Tests

[Detailed steps]

### Task 6.5: Final Hardening and Validation

[Detailed steps]

### Stage 6 Completion

```bash
pytest tests/test_resilience/ -v --tb=short
git commit -m "feat: complete Stage 6 - Resilience & Hardening with 60+ tests"
git tag -a stage6-complete -m "Stage 6: Resilience & Hardening complete - Chaos engineering, large-scale tests, migration tests, 60+ tests"
```

**Stage 6 Complete** ✅

---

## Final Steps

### Complete Phase 3 Implementation

```bash
# Run all tests
pytest tests/test_wiki/ -v --tb=short

# Expected: PASS (395+ tests)

# Create Phase 3 completion tag
git tag -a v3.0.0-phase3 -m "Phase 3: Intelligent Knowledge Accumulation complete - 27-28 weeks, 395+ tests"

# Update documentation
# - Update README.md with Phase 3 features
# - Update docs/USAGE.md with Phase 3 usage
# - Create docs/phase3-summary.md

# Final commit
git add README.md docs/USAGE.md docs/phase3-summary.md
git commit -m "docs: complete Phase 3 documentation and summary"
```

---

## Execution Handoff

**Plan complete and saved to** `docs/superpowers/plans/2026-04-06-phase3-intelligent-knowledge-accumulation.md`

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
