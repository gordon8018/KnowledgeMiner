# KnowledgeMiner 4.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete rewrite of KnowledgeMiner based on LLM Wiki pattern with three-layer architecture (Raw Sources → Enhanced Models → Wiki Models)

**Architecture:** Three-layer design where raw sources are immutable inputs, enhanced models handle processing/discovery, and wiki models provide persistent markdown storage with Obsidian compatibility

**Tech Stack:** Python 3.13, Pydantic, NumPy, OpenAI API (embeddings), Markdown, YAML

**Implementation Strategy:** Complete rewrite from scratch on new branch, not gradual migration

**Timeline:** 4 weeks (20 working days)

---

## Week 1: Foundation and Raw Layer

### Day 1-2: Project Structure and Base Models

#### Task 1.1: Create project structure

**Files:**
- Create: `src/__init__.py`
- Create: `src/raw/__init__.py`
- Create: `src/enhanced/__init__.py`
- Create: `src/wiki/__init__.py`
- Create: `src/raw/models.py`
- Create: `src/enhanced/models.py`
- Create: `src/wiki/models.py`
- Create: `config/__init__.py`
- Create: `config/schema.yaml`
- Create: `tests/__init__.py`
- Create: `tests/test_raw/__init__.py`
- Create: `tests/test_enhanced/__init__.py`
- Create: `tests/test_wiki/__init__.py`
- Create: `tests/test_integration/__init__.py`

- [ ] **Step 1: Create directory structure**

Run:
```bash
mkdir -p src/raw src/enhanced src/wiki
mkdir -p tests/test_raw tests/test_enhanced tests/test_wiki tests/test_integration
mkdir -p config
mkdir -p raw/papers raw/articles raw/reports raw/notes
mkdir -p wiki/entities wiki/concepts wiki/sources wiki/synthesis wiki/comparisons
```

Expected: All directories created

- [ ] **Step 2: Create __init__.py files**

Run:
```bash
touch src/__init__.py src/raw/__init__.py src/enhanced/__init__.py src/wiki/__init__.py
touch tests/__init__.py tests/test_raw/__init__.py tests/test_enhanced/__init__.py
touch tests/test_wiki/__init__.py tests/test_integration/__init__.py
touch config/__init__.py
```

Expected: All __init__.py files created

- [ ] **Step 3: Create base model files**

Run:
```bash
touch src/raw/models.py src/enhanced/models.py src/wiki/models.py
touch config/schema.yaml
```

Expected: Base model files created

- [ ] **Step 4: Initialize git repository (if not already)**

Run:
```bash
git init
git add .
git commit -m "feat: create KnowledgeMiner 4.0 project structure"
```

Expected: Git repository initialized with initial commit

---

#### Task 1.2: Define enhanced models

**Files:**
- Modify: `src/enhanced/models.py`

- [ ] **Step 1: Write the test for EnhancedConcept**

Create: `tests/test_enhanced/test_models.py`
```python
import pytest
import numpy as np
from datetime import datetime
from src.enhanced.models import EnhancedConcept, ConceptType

def test_enhanced_concept_creation():
    """Test creating an EnhancedConcept"""
    concept = EnhancedConcept(
        name="Test Concept",
        type=ConceptType.ENTITY,
        definition="A test concept for testing",
        confidence=0.8
    )

    assert concept.name == "Test Concept"
    assert concept.type == ConceptType.ENTITY
    assert concept.definition == "A test concept for testing"
    assert concept.confidence == 0.8
    assert concept.embeddings is None
    assert concept.properties == {}
    assert concept.relations == []
    assert concept.evidence == []

def test_enhanced_concept_with_embeddings():
    """Test EnhancedConcept with embeddings"""
    embeddings = np.array([0.1, 0.2, 0.3])
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        embeddings=embeddings
    )

    assert concept.embeddings is not None
    assert np.array_equal(concept.embeddings, embeddings)

def test_enhanced_concept_add_evidence():
    """Test adding evidence to concept"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    concept.add_evidence("source1.md", "Quote here", 0.9)

    assert len(concept.evidence) == 1
    assert concept.evidence[0]["source"] == "source1.md"
    assert concept.evidence[0]["confidence"] == 0.9

def test_enhanced_concept_add_relation():
    """Test adding relation to concept"""
    concept = EnhancedConcept(
        name="Concept1",
        type=ConceptType.ABSTRACT,
        definition="Test"
    )

    concept.add_relation("Concept2")

    assert "Concept2" in concept.relations

def test_enhanced_concept_update_confidence():
    """Test updating confidence"""
    concept = EnhancedConcept(
        name="Test",
        type=ConceptType.ABSTRACT,
        definition="Test",
        confidence=0.5
    )

    concept.update_confidence(0.9)

    assert concept.confidence == 0.9
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_enhanced/test_models.py::test_enhanced_concept_creation -v
```

Expected: FAIL with "ImportError: cannot import name EnhancedConcept"

- [ ] **Step 3: Implement EnhancedConcept model**

Modify: `src/enhanced/models.py`
```python
"""
Enhanced models for KnowledgeMiner 4.0
These models are used in the processing layer for knowledge extraction and discovery
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field


class ConceptType(str, Enum):
    """Types of concepts"""
    ENTITY = "entity"
    ABSTRACT = "abstract"
    RELATION = "relation"
    METHOD = "method"


class TemporalInfo(BaseModel):
    """Temporal information for concepts"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class EnhancedConcept(BaseModel):
    """
    Enhanced concept model for knowledge extraction and analysis

    This model represents a concept with full feature support including
    embeddings, confidence scoring, evidence tracking, and relation management
    """

    # Basic attributes
    name: str
    type: ConceptType
    definition: str

    # Enhanced features
    embeddings: Optional[np.ndarray] = Field(default=None)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Knowledge associations
    properties: Dict[str, Any] = Field(default_factory=dict)
    relations: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    temporal_info: Optional[TemporalInfo] = Field(default=None)
    source_documents: List[str] = Field(default_factory=list)

    def add_evidence(self, source: str, quote: str, confidence: float) -> None:
        """
        Add supporting evidence for this concept

        Args:
            source: Source document identifier
            quote: Relevant quote from source
            confidence: Confidence of this evidence (0-1)
        """
        evidence_entry = {
            "source": source,
            "quote": quote,
            "confidence": confidence,
            "added_at": datetime.now().isoformat()
        }
        self.evidence.append(evidence_entry)

    def add_relation(self, concept_name: str) -> None:
        """
        Add a related concept

        Args:
            concept_name: Name of related concept
        """
        if concept_name not in self.relations:
            self.relations.append(concept_name)

    def update_confidence(self, confidence: float) -> None:
        """
        Update confidence score

        Args:
            confidence: New confidence score (0-1)
        """
        if 0.0 <= confidence <= 1.0:
            self.confidence = confidence
        else:
            raise ValueError("Confidence must be between 0 and 1")

    class Config:
        arbitrary_types_allowed = True  # Allow np.ndarray
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_enhanced/test_models.py -v
```

Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_enhanced/test_models.py src/enhanced/models.py
git commit -m "feat: implement EnhancedConcept model with full feature support"
```

---

#### Task 1.3: Define EnhancedDocument model

**Files:**
- Modify: `src/enhanced/models.py`
- Create: `tests/test_enhanced/test_enhanced_document.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_enhanced/test_enhanced_document.py`
```python
import pytest
from src.enhanced.models import EnhancedDocument, SourceType, DocumentMetadata

def test_enhanced_document_creation():
    """Test creating an EnhancedDocument"""
    metadata = DocumentMetadata(
        title="Test Document",
        tags=["test", "example"],
        file_path="/path/to/doc.md"
    )

    doc = EnhancedDocument(
        source_type=SourceType.FILE,
        content="# Test Content\nThis is a test document.",
        metadata=metadata
    )

    assert doc.source_type == SourceType.FILE
    assert doc.content == "# Test Content\nThis is a test document."
    assert doc.metadata.title == "Test Document"
    assert doc.quality_score == 0.5
    assert doc.concepts == []

def test_enhanced_document_add_concept():
    """Test adding a concept to document"""
    from src.enhanced.models import EnhancedConcept, ConceptType

    doc = EnhancedDocument(
        source_type=SourceType.TEXT,
        content="Test content",
        metadata=DocumentMetadata(title="Test")
    )

    concept = EnhancedConcept(
        name="TestConcept",
        type=ConceptType.ABSTRACT,
        definition="A test concept"
    )

    doc.add_concept(concept)

    assert len(doc.concepts) == 1
    assert doc.concepts[0].name == "TestConcept"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_enhanced/test_enhanced_document.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement EnhancedDocument model**

Add to `src/enhanced/models.py`:
```python
# Add these classes after EnhancedConcept

class SourceType(str, Enum):
    """Types of sources"""
    FILE = "file"
    URL = "url"
    TEXT = "text"


class DocumentMetadata(BaseModel):
    """Metadata for documents"""
    title: str
    tags: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None
    url: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    date: Optional[datetime] = None


class Relation(BaseModel):
    """Relation between concepts"""
    source: str
    target: str
    relation_type: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class EnhancedDocument(BaseModel):
    """
    Enhanced document model for document analysis

    Represents a document with full feature support for concept extraction,
    relation detection, and quality scoring
    """

    source_type: SourceType
    content: str

    # Metadata
    metadata: DocumentMetadata

    # Enhanced features
    embeddings: Optional[np.ndarray] = Field(default=None)
    concepts: List[EnhancedConcept] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)

    def add_concept(self, concept: EnhancedConcept) -> None:
        """
        Add a concept to this document

        Args:
            concept: EnhancedConcept instance
        """
        self.concepts.append(concept)

    def find_concepts_by_type(self, concept_type: ConceptType) -> List[EnhancedConcept]:
        """
        Find all concepts of a specific type

        Args:
            concept_type: Type of concept to find

        Returns:
            List of concepts of the specified type
        """
        return [c for c in self.concepts if c.type == concept_type]

    class Config:
        arbitrary_types_allowed = True
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_enhanced/test_enhanced_document.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_enhanced/test_enhanced_document.py src/enhanced/models.py
git commit -m "feat: implement EnhancedDocument model with concept management"
```

---

#### Task 1.4: Define DiscoveryResult model

**Files:**
- Modify: `src/enhanced/models.py`
- Create: `tests/test_enhanced/test_discovery_result.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_enhanced/test_discovery_result.py`
```python
import pytest
from datetime import datetime
from src.enhanced.models import DiscoveryResult, DiscoveryType

def test_discovery_result_creation():
    """Test creating a DiscoveryResult"""
    result = DiscoveryResult(
        result_type=DiscoveryType.PATTERN,
        summary="Found a recurring pattern in the data",
        significance_score=0.8,
        confidence=0.75
    )

    assert result.result_type == DiscoveryType.PATTERN
    assert result.significance_score == 0.8
    assert result.confidence == 0.75
    assert result.affected_concepts == []
    assert isinstance(result.discovered_at, datetime)

def test_discovery_result_with_evidence():
    """Test DiscoveryResult with evidence"""
    result = DiscoveryResult(
        result_type=DiscoveryType.INSIGHT,
        summary="New insight discovered",
        significance_score=0.9,
        confidence=0.85,
        affected_concepts=["concept1", "concept2"],
        evidence=[
            {"source": "doc1.md", "quote": "Evidence here"}
        ]
    )

    assert len(result.affected_concepts) == 2
    assert len(result.evidence) == 1
    assert result.evidence[0]["source"] == "doc1.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_enhanced/test_discovery_result.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement DiscoveryResult model**

Add to `src/enhanced/models.py`:
```python
# Add these classes after EnhancedDocument

class DiscoveryType(str, Enum):
    """Types of discoveries"""
    PATTERN = "pattern"
    GAP = "gap"
    INSIGHT = "insight"
    CONTRADICTION = "contradiction"


class DiscoveryResult(BaseModel):
    """
    Knowledge discovery result

    Represents a discovery made by the discovery engine including
    patterns, gaps, insights, or contradictions
    """

    # Discovery type
    result_type: DiscoveryType

    # Content
    summary: str
    significance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Evidence
    affected_concepts: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.now)
    source_documents: List[str] = Field(default_factory=list)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_enhanced/test_discovery_result.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_enhanced/test_discovery_result.py src/enhanced/models.py
git commit -m "feat: implement DiscoveryResult model for knowledge discoveries"
```

---

### Day 3-4: Raw Source Layer

#### Task 1.5: Implement SourceLoader

**Files:**
- Create: `src/raw/source_loader.py`
- Create: `tests/test_raw/test_source_loader.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_raw/test_source_loader.py`
```python
import pytest
import os
from src.raw.source_loader import SourceLoader, SourceLoadError

def test_load_markdown_file():
    """Test loading a markdown file"""
    # Create test file
    test_file = "raw/tests/test.md"
    os.makedirs("raw/tests", exist_ok=True)
    with open(test_file, "w") as f:
        f.write("# Test Document\n\nThis is a test.")

    loader = SourceLoader()
    source = loader.load(test_file)

    assert source.content == "# Test Document\n\nThis is a test."
    assert source.path == test_file

    # Cleanup
    os.remove(test_file)

def test_load_nonexistent_file():
    """Test loading a file that doesn't exist"""
    loader = SourceLoader()

    with pytest.raises(SourceLoadError):
        loader.load("nonexistent.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_raw/test_source_loader.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement SourceLoader**

Create: `src/raw/source_loader.py`
```python
"""
Source loading functionality for Raw Sources layer
"""

import os
from pathlib import Path
from typing import Optional


class SourceLoadError(Exception):
    """Raised when source fails to load"""
    pass


class RawSource:
    """Represents a raw source document"""
    def __init__(self, content: str, path: str):
        self.content = content
        self.path = path
        self.filename = os.path.basename(path)


class SourceLoader:
    """
    Loads raw source documents from disk

    Raw sources are immutable - they are never modified by the system
    """

    def load(self, path: str) -> RawSource:
        """
        Load a raw source from disk

        Args:
            path: Path to the source file

        Returns:
            RawSource instance

        Raises:
            SourceLoadError: If file cannot be loaded
        """
        if not os.path.exists(path):
            raise SourceLoadError(f"File not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return RawSource(content=content, path=path)

        except Exception as e:
            raise SourceLoadError(f"Failed to load {path}: {e}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_raw/test_source_loader.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_raw/test_source_loader.py src/raw/source_loader.py
git commit -m "feat: implement SourceLoader for raw sources"
```

---

#### Task 1.6: Implement SourceParser

**Files:**
- Create: `src/raw/source_parser.py`
- Create: `tests/test_raw/test_source_parser.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_raw/test_source_parser.py`
```python
import pytest
from src.raw.source_parser import SourceParser, SourceParseError
from src.raw.source_loader import RawSource

def test_parse_markdown_with_frontmatter():
    """Test parsing markdown with YAML frontmatter"""
    content = """---
title: "Test Paper"
source_type: "paper"
authors: ["Author A", "Author B"]
tags: ["test", "example"]
---

# Main Content

This is the main content of the document.
"""

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert parsed["title"] == "Test Paper"
    assert parsed["source_type"] == "paper"
    assert parsed["authors"] == ["Author A", "Author B"]
    assert parsed["tags"] == ["test", "example"]
    assert parsed["content"] == "# Main Content\n\nThis is the main content of the document."

def test_parse_markdown_without_frontmatter():
    """Test parsing markdown without frontmatter"""
    content = "# Simple Document\n\nNo frontmatter here."

    raw_source = RawSource(content=content, path="test.md")
    parser = SourceParser()

    parsed = parser.parse(raw_source)

    assert parsed["content"] == "# Simple Document\n\nNo frontmatter here."
    assert parsed["title"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_raw/test_source_parser.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement SourceParser**

Create: `src/raw/source_parser.py`
```python
"""
Source parsing functionality for Raw Sources layer
"""

import re
from typing import Dict, Any
from src.raw.source_loader import RawSource


class SourceParseError(Exception):
    """Raised when source fails to parse"""
    pass


class SourceParser:
    """
    Parses raw source documents and extracts frontmatter and content
    """

    def parse(self, source: RawSource) -> Dict[str, Any]:
        """
        Parse a raw source and extract frontmatter and content

        Args:
            source: RawSource instance

        Returns:
            Dictionary with frontmatter fields and content
        """
        content = source.content

        # Check for YAML frontmatter
        frontmatter_pattern = r"^---\n(.*?)\n---\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter_text, body_content = match.groups()
            frontmatter = self._parse_yaml_frontmatter(frontmatter_text)

            result = {
                **frontmatter,
                "content": body_content.strip(),
                "path": source.path
            }
        else:
            # No frontmatter
            result = {
                "content": content.strip(),
                "path": source.path
            }

        return result

    def _parse_yaml_frontmatter(self, text: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter (simple implementation)

        Args:
            text: YAML frontmatter text

        Returns:
            Dictionary of frontmatter fields
        """
        result = {}

        for line in text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle quoted strings
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("[") and value.endswith("]"):
                    # Handle lists
                    value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]

                result[key] = value

        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_raw/test_source_parser.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_raw/test_source_parser.py src/raw/source_parser.py
git commit -m "feat: implement SourceParser with frontmatter support"
```

---

### Day 5: Concept Extractor (Basic)

#### Task 1.7: Implement basic ConceptExtractor

**Files:**
- Create: `src/enhanced/extractors/__init__.py`
- Create: `src/enhanced/extractors/concept_extractor.py`
- Create: `tests/test_enhanced/test_concept_extractor.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_enhanced/test_concept_extractor.py`
```python
import pytest
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType

def test_extract_concepts_from_simple_text():
    """Test extracting concepts from simple text"""
    content = """
    Machine Learning is a subset of Artificial Intelligence.
    Deep Learning is a type of Machine Learning.
    """

    doc = EnhancedDocument(
        source_type=SourceType.TEXT,
        content=content,
        metadata=DocumentMetadata(title="ML Test")
    )

    extractor = ConceptExtractor()
    concepts = extractor.extract(doc)

    assert len(concepts) > 0
    # Should find key concepts like "Machine Learning", "Artificial Intelligence"
    concept_names = [c.name for c in concepts]
    assert any("Machine Learning" in name for name in concept_names)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_enhanced/test_concept_extractor.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement ConceptExtractor**

Create: `src/enhanced/extractors/__init__.py`:
```python
"""Enhanced layer extractors"""
```

Create: `src/enhanced/extractors/concept_extractor.py`:
```python
"""
Concept extraction functionality
"""

import re
from typing import List
from src.enhanced.models import EnhancedDocument, EnhancedConcept, ConceptType


class ConceptExtractor:
    """
    Extracts concepts from documents

    This is a basic implementation that extracts capitalized phrases
    that appear to be concepts
    """

    def extract(self, document: EnhancedDocument) -> List[EnhancedConcept]:
        """
        Extract concepts from a document

        Args:
            document: EnhancedDocument instance

        Returns:
            List of EnhancedConcept instances
        """
        concepts = []
        content = document.content

        # Simple pattern: Capitalized words/phrases (2-4 words)
        # This is a basic implementation - will be enhanced with LLM
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        matches = re.findall(pattern, content)

        # Filter unique concepts
        unique_matches = list(set(matches))

        for match in unique_matches:
            # Skip common words
            if self._is_common_word(match):
                continue

            concept = EnhancedConcept(
                name=match,
                type=ConceptType.ABSTRACT,
                definition=f"Concept: {match}",  # Will be enhanced with LLM
                confidence=0.5,
                source_documents=[document.metadata.file_path or "unknown"]
            )

            concepts.append(concept)

        return concepts

    def _is_common_word(self, phrase: str) -> bool:
        """Check if phrase is a common word to skip"""
        common_words = {
            "The", "This", "That", "These", "Those",
            "And", "But", "Or", "For", "Nor", "So", "Yet",
            "Is", "Are", "Was", "Were", "Be", "Been", "Being",
            "Have", "Has", "Had", "Do", "Does", "Did"
        }

        return phrase in common_words
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_enhanced/test_concept_extractor.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_enhanced/test_concept_extractor.py src/enhanced/extractors/
git commit -m "feat: implement basic ConceptExtractor"
```

---

## Week 2: Enhanced Layer and Discovery

### Day 6-7: Discovery Components

#### Task 2.1: Implement PatternDetector

**Files:**
- Create: `src/enhanced/discovery/__init__.py`
- Create: `src/enhanced/discovery/pattern_detector.py`
- Create: `tests/test_enhanced/test_pattern_detector.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_enhanced/test_pattern_detector.py`
```python
import pytest
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.enhanced.models import EnhancedConcept, ConceptType

def test_detect_recurring_patterns():
    """Test detecting recurring patterns in concepts"""
    concepts = [
        EnhancedConcept(
            name="Concept1",
            type=ConceptType.ABSTRACT,
            definition="Pattern A appears in context X",
            properties={"pattern": "A"}
        ),
        EnhancedConcept(
            name="Concept2",
            type=ConceptType.ABSTRACT,
            definition="Pattern A appears in context Y",
            properties={"pattern": "A"}
        )
    ]

    detector = PatternDetector()
    patterns = detector.detect(concepts)

    assert len(patterns) > 0
    # Should detect that pattern "A" appears in both concepts
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_enhanced/test_pattern_detector.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement PatternDetector**

Create: `src/enhanced/discovery/__init__.py`:
```python
"""Enhanced layer discovery components"""
```

Create: `src/enhanced/discovery/pattern_detector.py`:
```python
"""
Pattern detection functionality
"""

from collections import Counter
from typing import List
from src.enhanced.models import EnhancedConcept, DiscoveryResult, DiscoveryType


class PatternDetector:
    """
    Detects recurring patterns across concepts
    """

    def detect(self, concepts: List[EnhancedConcept]) -> List[DiscoveryResult]:
        """
        Detect patterns in a list of concepts

        Args:
            concepts: List of EnhancedConcept instances

        Returns:
            List of DiscoveryResult instances with type PATTERN
        """
        results = []

        # Look for recurring patterns in properties
        pattern_counter = Counter()

        for concept in concepts:
            if "pattern" in concept.properties:
                pattern = concept.properties["pattern"]
                pattern_counter[pattern] += 1

        # Find patterns that appear multiple times
        for pattern, count in pattern_counter.items():
            if count >= 2:  # Pattern appears at least twice
                result = DiscoveryResult(
                    result_type=DiscoveryType.PATTERN,
                    summary=f"Recurring pattern '{pattern}' found in {count} concepts",
                    significance_score=min(0.9, count * 0.3),
                    confidence=0.7,
                    affected_concepts=[c.name for c in concepts if "pattern" in c.properties and c.properties["pattern"] == pattern]
                )

                results.append(result)

        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_enhanced/test_pattern_detector.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_enhanced/test_pattern_detector.py src/enhanced/discovery/
git commit -m "feat: implement PatternDetector for recurring patterns"
```

---

#### Task 2.2: Implement GapAnalyzer

**Files:**
- Create: `src/enhanced/discovery/gap_analyzer.py`
- Create: `tests/test_enhanced/test_gap_analyzer.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_enhanced/test_gap_analyzer.py`
```python
import pytest
from src.enhanced.discovery.gap_analyzer import GapAnalyzer
from src.enhanced.models import EnhancedConcept, ConceptType

def test_analyze_knowledge_gaps():
    """Test analyzing knowledge gaps"""
    concepts = [
        EnhancedConcept(
            name="Concept1",
            type=ConceptType.ABSTRACT,
            definition="Well-defined concept",
            confidence=0.9
        ),
        EnhancedConcept(
            name="Concept2",
            type=ConceptType.ABSTRACT,
            definition="Poorly defined concept",
            confidence=0.3
        )
    ]

    analyzer = GapAnalyzer()
    gaps = analyzer.analyze(concepts)

    assert len(gaps) > 0
    # Should detect that Concept2 has low confidence (knowledge gap)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_enhanced/test_gap_analyzer.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement GapAnalyzer**

Create: `src/enhanced/discovery/gap_analyzer.py`:
```python
"""
Knowledge gap analysis functionality
"""

from typing import List
from src.enhanced.models import EnhancedConcept, DiscoveryResult, DiscoveryType


class GapAnalyzer:
    """
    Analyzes concepts to identify knowledge gaps
    """

    def analyze(self, concepts: List[EnhancedConcept]) -> List[DiscoveryResult]:
        """
        Analyze concepts for knowledge gaps

        Args:
            concepts: List of EnhancedConcept instances

        Returns:
            List of DiscoveryResult instances with type GAP
        """
        results = []

        for concept in concepts:
            # Low confidence indicates potential knowledge gap
            if concept.confidence < 0.5:
                result = DiscoveryResult(
                    result_type=DiscoveryType.GAP,
                    summary=f"Knowledge gap: '{concept.name}' has low confidence ({concept.confidence})",
                    significance_score=1.0 - concept.confidence,
                    confidence=0.8,
                    affected_concepts=[concept.name]
                )

                results.append(result)

            # Missing evidence
            if len(concept.evidence) == 0:
                result = DiscoveryResult(
                    result_type=DiscoveryType.GAP,
                    summary=f"Knowledge gap: '{concept.name}' has no supporting evidence",
                    significance_score=0.7,
                    confidence=0.9,
                    affected_concepts=[concept.name]
                )

                results.append(result)

        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_enhanced/test_gap_analyzer.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_enhanced/test_gap_analyzer.py src/enhanced/discovery/gap_analyzer.py
git commit -m "feat: implement GapAnalyzer for knowledge gaps"
```

---

#### Task 2.3: Implement InsightGenerator

**Files:**
- Create: `src/enhanced/discovery/insight_generator.py`
- Create: `tests/test_enhanced/test_insight_generator.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_enhanced/test_insight_generator.py`
```python
import pytest
from src.enhanced.discovery.insight_generator import InsightGenerator
from src.enhanced.models import EnhancedConcept, ConceptType

def test_generate_insights():
    """Test generating insights from concepts"""
    concepts = [
        EnhancedConcept(
            name="Concept1",
            type=ConceptType.ABSTRACT,
            definition="Definition 1",
            relations=["Concept2", "Concept3"]
        ),
        EnhancedConcept(
            name="Concept2",
            type=ConceptType.ABSTRACT,
            definition="Definition 2",
            relations=["Concept1"]
        )
    ]

    generator = InsightGenerator()
    insights = generator.generate(concepts)

    assert len(insights) > 0
    # Should generate insight about interconnected concepts
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_enhanced/test_insight_generator.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement InsightGenerator**

Create: `src/enhanced/discovery/insight_generator.py`:
```python
"""
Insight generation functionality
"""

from typing import List
from src.enhanced.models import EnhancedConcept, DiscoveryResult, DiscoveryType


class InsightGenerator:
    """
    Generates insights from concept relationships
    """

    def generate(self, concepts: List[EnhancedConcept]) -> List[DiscoveryResult]:
        """
        Generate insights from concepts

        Args:
            concepts: List of EnhancedConcept instances

        Returns:
            List of DiscoveryResult instances with type INSIGHT
        """
        results = []

        # Find highly connected concepts (hubs)
        for concept in concepts:
            if len(concept.relations) >= 3:
                result = DiscoveryResult(
                    result_type=DiscoveryType.INSIGHT,
                    summary=f"Insight: '{concept.name}' is a central concept connected to {len(concept.relations)} other concepts",
                    significance_score=min(0.9, len(concept.relations) * 0.2),
                    confidence=0.7,
                    affected_concepts=[concept.name] + concept.relations
                )

                results.append(result)

        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_enhanced/test_insight_generator.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_enhanced/test_insight_generator.py src/enhanced/discovery/insight_generator.py
git commit -m "feat: implement InsightGenerator for relationship insights"
```

---

### Day 8-9: Wiki Models and Writers

#### Task 2.4: Implement WikiPage model

**Files:**
- Modify: `src/wiki/models.py`
- Create: `tests/test_wiki/test_wiki_page.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_wiki/test_wiki_page.py`
```python
import pytest
from datetime import datetime
from src.wiki.models import WikiPage, PageType

def test_wiki_page_creation():
    """Test creating a WikiPage"""
    page = WikiPage(
        id="test-page",
        title="Test Page",
        page_type=PageType.CONCEPT,
        content="# Test Page\n\nThis is a test page."
    )

    assert page.id == "test-page"
    assert page.title == "Test Page"
    assert page.page_type == PageType.CONCEPT
    assert page.version == 1
    assert isinstance(page.created_at, datetime)
    assert page.links == []
    assert page.backlinks == []

def test_wiki_page_to_markdown():
    """Test converting WikiPage to markdown"""
    page = WikiPage(
        id="test",
        title="Test",
        page_type=PageType.CONCEPT,
        content="# Test\n\nContent here",
        frontmatter={"tags": ["test", "example"]}
    )

    markdown = page.to_markdown()

    assert "---" in markdown
    assert "tags:" in markdown
    assert "# Test" in markdown
    assert "Content here" in markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_wiki/test_wiki_page.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement WikiPage model**

Modify: `src/wiki/models.py`:
```python
"""
Wiki models for KnowledgeMiner 4.0
These models represent the persistent storage layer in markdown format
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PageType(str, Enum):
    """Types of wiki pages"""
    ENTITY = "entity"
    CONCEPT = "concept"
    SOURCE = "source"
    SYNTHESIS = "synthesis"
    COMPARISON = "comparison"


class UpdateType(str, Enum):
    """Types of wiki updates"""
    INGEST = "ingest"
    QUERY = "query"
    LINT = "lint"


class WikiPage(BaseModel):
    """
    Wiki page model for persistent markdown storage

    Represents a page in the wiki with full support for versioning,
    linking, and Obsidian compatibility
    """

    # Page identification
    id: str
    title: str
    page_type: PageType

    # Content
    content: str
    frontmatter: Dict[str, Any] = Field(default_factory=dict)

    # Version control
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Links
    links: List[str] = Field(default_factory=list)
    backlinks: List[str] = Field(default_factory=list)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    sources_count: int = Field(default=0)

    def to_markdown(self) -> str:
        """
        Convert wiki page to markdown format

        Returns:
            Markdown string with YAML frontmatter
        """
        lines = []

        # YAML frontmatter
        lines.append("---")
        for key, value in self.frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")

        # Content
        lines.append(self.content)

        return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_wiki/test_wiki_page.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wiki/test_wiki_page.py src/wiki/models.py
git commit -m "feat: implement WikiPage model with markdown conversion"
```

---

#### Task 2.5: Implement WikiUpdate and WikiIndex models

**Files:**
- Modify: `src/wiki/models.py`
- Create: `tests/test_wiki/test_wiki_models.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_wiki/test_wiki_models.py`
```python
import pytest
from datetime import datetime
from src.wiki.models import WikiUpdate, WikiIndex, UpdateType, IndexEntry

def test_wiki_update_creation():
    """Test creating a WikiUpdate"""
    update = WikiUpdate(
        timestamp=datetime.now(),
        update_type=UpdateType.INGEST,
        page_id="test-page",
        changes="Created new page",
        parent_version=0
    )

    assert update.update_type == UpdateType.INGEST
    assert update.page_id == "test-page"
    assert update.changes == "Created new page"

def test_wiki_index():
    """Test WikiIndex operations"""
    index = WikiIndex()

    entry = IndexEntry(
        page_id="test",
        title="Test Page",
        summary="A test page"
    )

    index.add_entry("concepts", entry)

    assert "concepts" in index.categories
    assert len(index.categories["concepts"]) == 1
    assert index.categories["concepts"][0].page_id == "test"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_wiki/test_wiki_models.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement WikiUpdate and WikiIndex**

Add to `src/wiki/models.py`:
```python
# Add these classes after WikiPage

class IndexEntry(BaseModel):
    """Entry in the wiki index"""
    page_id: str
    title: str
    summary: str
    tags: List[str] = Field(default_factory=list)
    date: Optional[datetime] = None


class WikiUpdate(BaseModel):
    """
    Wiki update record for tracking changes in log.md

    Each update represents a change to a wiki page
    """

    timestamp: datetime
    update_type: UpdateType
    page_id: str
    changes: str
    parent_version: int


class WikiIndex(BaseModel):
    """
    Wiki index for organizing all pages

    Used to generate index.md with categorized page listings
    """

    categories: Dict[str, List[IndexEntry]] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

    def add_entry(self, category: str, entry: IndexEntry) -> None:
        """
        Add an entry to a category

        Args:
            category: Category name (e.g., "concepts", "entities")
            entry: IndexEntry instance
        """
        if category not in self.categories:
            self.categories[category] = []

        self.categories[category].append(entry)
        self.last_updated = datetime.now()

    def to_markdown(self) -> str:
        """
        Convert index to markdown format

        Returns:
            Markdown string for index.md
        """
        lines = []
        lines.append("# KnowledgeMiner Wiki Index")
        lines.append("")
        lines.append(f"*Last updated: {self.last_updated.strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")

        for category, entries in self.categories.items():
            lines.append(f"## {category.title()}")
            lines.append("")

            for entry in entries:
                tags_str = ", ".join(entry.tags) if entry.tags else ""
                lines.append(f"- [[{entry.page_id}|{entry.title}]] - {entry.summary}")
                if tags_str:
                    lines.append(f"  Tags: {tags_str}")
                lines.append("")

        return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_wiki/test_wiki_models.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wiki/test_wiki_models.py src/wiki/models.py
git commit -m "feat: implement WikiUpdate and WikiIndex models"
```

---

### Day 10: Basic Ingest Flow

#### Task 2.6: Implement basic PageWriter

**Files:**
- Create: `src/wiki/writers/page_writer.py`
- Create: `tests/test_wiki/test_page_writer.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_wiki/test_page_writer.py`
```python
import pytest
import os
from src.wiki.writers.page_writer import PageWriter
from src.wiki.models import WikiPage, PageType

def test_write_wiki_page():
    """Test writing a wiki page to disk"""
    page = WikiPage(
        id="test-page",
        title="Test Page",
        page_type=PageType.CONCEPT,
        content="# Test\n\nContent here"
    )

    writer = PageWriter()
    writer.write(page, "wiki/concepts/")

    # Check file exists
    assert os.path.exists("wiki/concepts/test-page.md")

    # Check content
    with open("wiki/concepts/test-page.md", "r") as f:
        content = f.read()
    assert "# Test" in content
    assert "Content here" in content

    # Cleanup
    os.remove("wiki/concepts/test-page.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_wiki/test_page_writer.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement PageWriter**

Create: `src/wiki/writers/__init__.py`:
```python
"""Wiki writers"""
```

Create: `src/wiki/writers/page_writer.py`:
```python
"""
Wiki page writing functionality
"""

import os
from pathlib import Path
from src.wiki.models import WikiPage


class PageWriter:
    """
    Writes wiki pages to disk as markdown files
    """

    def write(self, page: WikiPage, directory: str) -> str:
        """
        Write a wiki page to disk

        Args:
            page: WikiPage instance
            directory: Directory to write to (e.g., "wiki/concepts/")

        Returns:
            Full path to written file
        """
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        # Generate filename
        filename = f"{page.id}.md"
        filepath = os.path.join(directory, filename)

        # Convert to markdown
        markdown_content = page.to_markdown()

        # Write to disk
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return filepath
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_wiki/test_page_writer.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wiki/test_page_writer.py src/wiki/writers/
git commit -m "feat: implement PageWriter for wiki markdown files"
```

---

## Week 3: Wiki Operations and Core Flows

### Day 11-12: Query Flow

#### Task 3.1: Implement IndexSearcher

**Files:**
- Create: `src/wiki/operations/index_searcher.py`
- Create: `tests/test_wiki/test_index_searcher.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_wiki/test_index_searcher.py`
```python
import pytest
from src.wiki.operations.index_searcher import IndexSearcher

def test_search_index():
    """Test searching wiki index"""
    # Create a test index
    index_content = """
    # KnowledgeMiner Wiki Index

    ## Concepts
    - [[concept1|Machine Learning]] - A subset of AI
    - [[concept2|Deep Learning]] - A type of ML

    ## Entities
    - [[entity1|OpenAI]] - AI company
    """

    with open("wiki/index.md", "w") as f:
        f.write(index_content)

    searcher = IndexSearcher()
    results = searcher.search("machine learning")

    assert len(results) > 0
    assert "concept1" in results

    # Cleanup
    import os
    os.remove("wiki/index.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_wiki/test_index_searcher.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement IndexSearcher**

Create: `src/wiki/operations/__init__.py`:
```python
"""Wiki operations"""
```

Create: `src/wiki/operations/index_searcher.py`:
```python
"""
Index searching functionality for wiki
"""

import os
import re
from typing import List


class IndexSearcher:
    """
    Searches wiki index.md to find relevant pages
    """

    def search(self, keywords: str) -> List[str]:
        """
        Search index for keywords

        Args:
            keywords: Search keywords

        Returns:
            List of page IDs matching the search
        """
        results = []
        index_path = "wiki/index.md"

        if not os.path.exists(index_path):
            return results

        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple keyword matching (will be enhanced with embeddings)
        # Look for links containing keywords
        pattern = r'\[\[([^\]|]+)'
        matches = re.findall(pattern, content)

        keywords_lower = keywords.lower()
        for match in matches:
            if keywords_lower in match.lower():
                results.append(match)

        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_wiki/test_index_searcher.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wiki/test_index_searcher.py src/wiki/operations/index_searcher.py
git commit -m "feat: implement IndexSearcher for wiki queries"
```

---

#### Task 3.2: Implement PageReader

**Files:**
- Create: `src/wiki/operations/page_reader.py`
- Create: `tests/test_wiki/test_page_reader.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_wiki/test_page_reader.py`
```python
import pytest
import os
from src.wiki.operations.page_reader import PageReader

def test_read_page():
    """Test reading a wiki page"""
    # Create test page
    os.makedirs("wiki/concepts", exist_ok=True)
    with open("wiki/concepts/test.md", "w") as f:
        f.write("# Test Concept\n\nThis is a test concept.")

    reader = PageReader()
    content = reader.read("test")

    assert "Test Concept" in content
    assert "test concept" in content.lower()

    # Cleanup
    os.remove("wiki/concepts/test.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_wiki/test_page_reader.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement PageReader**

Create: `src/wiki/operations/page_reader.py`:
```python
"""
Page reading functionality for wiki
"""

import os
from glob import glob


class PageReader:
    """
    Reads wiki pages from disk
    """

    def read(self, page_id: str) -> str:
        """
        Read a wiki page by ID

        Args:
            page_id: Page identifier (filename without .md)

        Returns:
            Page content as string

        Raises:
            FileNotFoundError: If page not found
        """
        # Search in common locations
        search_paths = [
            f"wiki/entities/{page_id}.md",
            f"wiki/concepts/{page_id}.md",
            f"wiki/sources/{page_id}.md",
            f"wiki/synthesis/{page_id}.md",
            f"wiki/comparisons/{page_id}.md"
        ]

        for path in search_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

        raise FileNotFoundError(f"Page not found: {page_id}")

    def list_all(self) -> List[str]:
        """
        List all wiki pages

        Returns:
            List of page IDs
        """
        patterns = [
            "wiki/entities/*.md",
            "wiki/concepts/*.md",
            "wiki/sources/*.md",
            "wiki/synthesis/*.md",
            "wiki/comparisons/*.md"
        ]

        page_ids = []
        for pattern in patterns:
            files = glob(pattern)
            for file in files:
                # Extract page ID from filename
                page_id = os.path.basename(file).replace(".md", "")
                page_ids.append(page_id)

        return page_ids
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_wiki/test_page_reader.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wiki/test_page_reader.py src/wiki/operations/page_reader.py
git commit -m "feat: implement PageReader for wiki content"
```

---

### Day 13: Lint Flow

#### Task 3.3: Implement basic Lint functionality

**Files:**
- Create: `src/wiki/operations/lint.py`
- Create: `tests/test_wiki/test_lint.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_wiki/test_lint.py`
```python
import pytest
import os
from src.wiki.operations.lint import lint_wiki, OrphanDetector

def test_detect_orphan_pages():
    """Test detecting orphan pages (no inbound links)"""
    # Create test pages
    os.makedirs("wiki/concepts", exist_ok=True)
    with open("wiki/concepts/orphan.md", "w") as f:
        f.write("# Orphan Page\n\nThis page has no links.")
    with open("wiki/concepts/linked.md", "w") as f:
        f.write("# Linked Page\n\nThis links to [[orphan]].")

    detector = OrphanDetector()
    orphans = detector.find(["wiki/concepts/orphan.md", "wiki/concepts/linked.md"])

    assert "orphan.md" in orphans

    # Cleanup
    os.remove("wiki/concepts/orphan.md")
    os.remove("wiki/concepts/linked.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_wiki/test_lint.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement basic Lint**

Create: `src/wiki/operations/lint.py`:
```python
"""
Wiki linting functionality for health checks
"""

import os
import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class LintReport:
    """Report from linting wiki"""
    total_pages: int
    issues_found: int
    issues_fixed: int
    recommendations: List[str]


class OrphanDetector:
    """
    Detects orphan pages (pages with no inbound links)
    """

    def find(self, page_paths: List[str]) -> List[str]:
        """
        Find orphan pages

        Args:
            page_paths: List of page file paths

        Returns:
            List of orphan page filenames
        """
        # Collect all links from all pages
        all_links = set()

        for page_path in page_paths:
            if not os.path.exists(page_path):
                continue

            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all wikilinks
            pattern = r'\[\[([^\]|]+)'
            matches = re.findall(pattern, content)
            all_links.update(matches)

        # Find orphans (pages not linked to by any other page)
        orphans = []
        for page_path in page_paths:
            page_id = os.path.basename(page_path).replace(".md", "")

            # Convert page ID to link format (handle spaces, etc.)
            if page_id not in all_links:
                # Check if it's a self-link (doesn't count as orphan)
                is_self_linked = False
                with open(page_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if f"[[{page_id}]]" in content or f"[[{page_id}|" in content:
                        is_self_linked = True

                if not is_self_linked:
                    orphans.append(page_id)

        return orphans


def lint_wiki() -> LintReport:
    """
    Lint the wiki and generate a report

    Returns:
        LintReport with findings
    """
    from src.wiki.operations.page_reader import PageReader

    reader = PageReader()
    all_pages = reader.list_all()

    issues = []
    fixes = []

    # Check for orphans
    detector = OrphanDetector()
    page_paths = [f"wiki/concepts/{p}.md" for p in all_pages]
    orphans = detector.find(page_paths)

    for orphan in orphans:
        issues.append(f"Orphan page: {orphan}")

    return LintReport(
        total_pages=len(all_pages),
        issues_found=len(issues),
        issues_fixed=len(fixes),
        recommendations=[]
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_wiki/test_lint.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wiki/test_lint.py src/wiki/operations/lint.py
git commit -m "feat: implement basic lint functionality with orphan detection"
```

---

### Day 14-15: Integration Tests

#### Task 3.4: Write integration tests for ingest flow

**Files:**
- Create: `tests/test_integration/test_ingest_flow.py`

- [ ] **Step 1: Write the integration test**

Create: `tests/test_integration/test_ingest_flow.py`:
```python
import pytest
import os
from src.raw.source_loader import SourceLoader
from src.raw.source_parser import SourceParser
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.wiki.writers.page_writer import PageWriter
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType

def test_full_ingest_flow():
    """Test complete ingest flow from source to wiki"""
    # Create test source
    os.makedirs("raw/tests", exist_ok=True)
    test_content = """---
title: "Test Paper"
source_type: "paper"
tags: ["test"]
---

# Machine Learning

Machine Learning is a subset of Artificial Intelligence.
Deep Learning is a type of Machine Learning.
"""

    with open("raw/tests/test_paper.md", "w") as f:
        f.write(test_content)

    # Load source
    loader = SourceLoader()
    source = loader.load("raw/tests/test_paper.md")

    assert source.content == test_content

    # Parse source
    parser = SourceParser()
    parsed = parser.parse(source)

    assert parsed["title"] == "Test Paper"
    assert "Machine Learning" in parsed["content"]

    # Create enhanced document
    doc = EnhancedDocument(
        source_type=SourceType.FILE,
        content=parsed["content"],
        metadata=DocumentMetadata(
            title=parsed["title"],
            tags=parsed.get("tags", []),
            file_path=source.path
        )
    )

    # Extract concepts
    extractor = ConceptExtractor()
    concepts = extractor.extract(doc)

    assert len(concepts) > 0

    # Detect patterns
    patterns = PatternDetector().detect(concepts)

    # Write to wiki
    writer = PageWriter()

    # Create a wiki page for the source
    from src.wiki.models import WikiPage, PageType
    source_page = WikiPage(
        id="test_paper",
        title=parsed["title"],
        page_type=PageType.SOURCE,
        content=f"# {parsed['title']}\n\n{parsed['content'][:200]}...",
        frontmatter={"tags": parsed.get("tags", [])}
    )

    filepath = writer.write(source_page, "wiki/sources/")

    assert os.path.exists(filepath)

    # Cleanup
    os.remove("raw/tests/test_paper.md")
    os.remove(filepath)
```

- [ ] **Step 2: Run integration test**

Run:
```bash
pytest tests/test_integration/test_ingest_flow.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration/test_ingest_flow.py
git commit -m "test: add integration test for full ingest flow"
```

---

## Week 4: Integration, Migration, and Polish

### Day 16-17: Data Migration

#### Task 4.1: Create migration scripts

**Files:**
- Create: `scripts/migrate_sources.py`
- Create: `scripts/rebuild_wiki.py`

- [ ] **Step 1: Create source migration script**

Create: `scripts/migrate_sources.py`:
```python
"""
Migrate sources from old KnowledgeMiner output to new raw/ structure
"""

import os
import shutil
import glob
from pathlib import Path


def classify_source(filepath: str) -> str:
    """
    Classify a source file into a category

    Args:
        filepath: Path to source file

    Returns:
        Category name (papers/articles/reports/notes)
    """
    # Simple classification based on filename and content
    filename = os.path.basename(filepath).lower()

    if "paper" in filename or "arxiv" in filename or filename.endswith(".pdf"):
        return "papers"
    elif "report" in filename:
        return "reports"
    elif "note" in filename:
        return "notes"
    else:
        return "articles"


def add_frontmatter(filepath: str, category: str) -> None:
    """
    Add YAML frontmatter to a source file

    Args:
        filepath: Path to source file
        category: Category of the source
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if already has frontmatter
    if content.startswith("---"):
        return

    # Add basic frontmatter
    title = os.path.basename(filepath).replace(".md", "")

    frontmatter = f"""---
title: "{title}"
source_type: "{category}"
tags: []
---

"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)


def migrate_sources():
    """Migrate sources from old output/ to new raw/ structure"""
    # Scan old output directory
    old_sources = glob("output/**/*.md", recursive=True)

    if not old_sources:
        print("No sources found in output/ directory")
        return

    print(f"Found {len(old_sources)} sources to migrate")

    migrated = 0
    for source in old_sources:
        try:
            # Classify
            category = classify_source(source)

            # Add frontmatter
            add_frontmatter(source, category)

            # Move to new location
            filename = os.path.basename(source)
            new_path = f"raw/{category}/{filename}"

            os.makedirs(f"raw/{category}", exist_ok=True)
            shutil.move(source, new_path)

            print(f"Migrated: {source} -> {new_path}")
            migrated += 1

        except Exception as e:
            print(f"Error migrating {source}: {e}")

    print(f"\nMigration complete: {migrated}/{len(old_sources)} sources migrated")


if __name__ == "__main__":
    migrate_sources()
```

- [ ] **Step 2: Create wiki rebuild script**

Create: `scripts/rebuild_wiki.py`:
```python
"""
Rebuild wiki from sources after migration
"""

import os
import glob
from src.raw.source_loader import SourceLoader
from src.raw.source_parser import SourceParser
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.wiki.writers.page_writer import PageWriter
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType
from src.wiki.models import WikiPage, PageType


def rebuild_wiki():
    """Rebuild entire wiki from raw sources"""
    # Clear old wiki
    if os.path.exists("wiki"):
        shutil.rmtree("wiki")
    os.makedirs("wiki/entities")
    os.makedirs("wiki/concepts")
    os.makedirs("wiki/sources")
    os.makedirs("wiki/synthesis")
    os.makedirs("wiki/comparisons")

    # Get all sources
    sources = glob("raw/**/*.md", recursive=True)

    print(f"Found {len(sources)} sources")

    loader = SourceLoader()
    parser = SourceParser()
    extractor = ConceptExtractor()
    pattern_detector = PatternDetector()
    writer = PageWriter()

    for source_path in sources:
        try:
            print(f"Processing: {source_path}")

            # Load and parse
            source = loader.load(source_path)
            parsed = parser.parse(source)

            # Create enhanced document
            doc = EnhancedDocument(
                source_type=SourceType.FILE,
                content=parsed["content"],
                metadata=DocumentMetadata(
                    title=parsed.get("title", os.path.basename(source_path)),
                    tags=parsed.get("tags", []),
                    file_path=source_path
                )
            )

            # Extract concepts
            concepts = extractor.extract(doc)
            print(f"  Extracted {len(concepts)} concepts")

            # Detect patterns
            patterns = pattern_detector.detect(concepts)
            print(f"  Found {len(patterns)} patterns")

            # Create source page
            source_page = WikiPage(
                id=os.path.basename(source_path).replace(".md", ""),
                title=parsed.get("title", "Unknown"),
                page_type=PageType.SOURCE,
                content=f"# {parsed.get('title', 'Unknown')}\n\n{parsed['content'][:500]}...",
                frontmatter={
                    "tags": parsed.get("tags", []),
                    "sources_count": len(concepts)
                }
            )

            writer.write(source_page, "wiki/sources/")
            print(f"  Created source page")

        except Exception as e:
            print(f"  Error: {e}")

    print("\nWiki rebuild complete!")


if __name__ == "__main__":
    rebuild_wiki()
```

- [ ] **Step 3: Commit**

```bash
git add scripts/migrate_sources.py scripts/rebuild_wiki.py
git commit -m "feat: add migration scripts for data transfer"
```

---

### Day 18-19: Final Integration and Testing

#### Task 4.2: Create orchestrator

**Files:**
- Create: `src/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the test**

Create: `tests/test_orchestrator.py`:
```python
import pytest
from src.orchestrator import KnowledgeMinerOrchestrator

def test_orchestrator_initialization():
    """Test initializing the orchestrator"""
    orchestrator = KnowledgeMinerOrchestrator()

    assert orchestrator is not None
    assert orchestrator.source_loader is not None
    assert orchestrator.concept_extractor is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_orchestrator.py -v
```

Expected: FAIL with imports not found

- [ ] **Step 3: Implement orchestrator**

Create: `src/orchestrator.py`:
```python
"""
Main orchestrator for KnowledgeMiner 4.0

Coordinates all components and provides high-level API
"""

from typing import List, Optional
from src.raw.source_loader import SourceLoader
from src.raw.source_parser import SourceParser
from src.enhanced.extractors.concept_extractor import ConceptExtractor
from src.enhanced.discovery.pattern_detector import PatternDetector
from src.enhanced.discovery.gap_analyzer import GapAnalyzer
from src.enhanced.discovery.insight_generator import InsightGenerator
from src.wiki.writers.page_writer import PageWriter
from src.wiki.operations.index_searcher import IndexSearcher
from src.wiki.operations.page_reader import PageReader
from src.wiki.operations.lint import lint_wiki
from src.enhanced.models import EnhancedDocument, DocumentMetadata, SourceType
from src.wiki.models import WikiPage, PageType


class KnowledgeMinerOrchestrator:
    """
    Main orchestrator for KnowledgeMiner 4.0

    Provides high-level API for ingest, query, and lint operations
    """

    def __init__(self):
        """Initialize all components"""
        self.source_loader = SourceLoader()
        self.source_parser = SourceParser()
        self.concept_extractor = ConceptExtractor()

        # Discovery components
        self.pattern_detector = PatternDetector()
        self.gap_analyzer = GapAnalyzer()
        self.insight_generator = InsightGenerator()

        # Wiki components
        self.page_writer = PageWriter()
        self.index_searcher = IndexSearcher()
        self.page_reader = PageReader()

    def ingest(self, source_path: str) -> dict:
        """
        Ingest a source into the wiki

        Args:
            source_path: Path to source file

        Returns:
            Dictionary with ingest results
        """
        # Load and parse
        source = self.source_loader.load(source_path)
        parsed = self.source_parser.parse(source)

        # Create enhanced document
        doc = EnhancedDocument(
            source_type=SourceType.FILE,
            content=parsed["content"],
            metadata=DocumentMetadata(
                title=parsed.get("title", "Unknown"),
                tags=parsed.get("tags", []),
                file_path=source_path
            )
        )

        # Extract concepts
        concepts = self.concept_extractor.extract(doc)

        # Discover patterns
        patterns = self.pattern_detector.detect(concepts)

        # Create wiki page
        page = WikiPage(
            id=parsed.get("title", "unknown").replace(" ", "-").lower(),
            title=parsed.get("title", "Unknown"),
            page_type=PageType.SOURCE,
            content=f"# {parsed.get('title', 'Unknown')}\n\n{parsed['content'][:500]}...",
            frontmatter={
                "tags": parsed.get("tags", []),
                "sources_count": len(concepts)
            }
        )

        filepath = self.page_writer.write(page, "wiki/sources/")

        return {
            "source": source_path,
            "concepts_extracted": len(concepts),
            "patterns_found": len(patterns),
            "wiki_page": filepath
        }

    def query(self, question: str) -> dict:
        """
        Query the wiki

        Args:
            question: Query string

        Returns:
            Dictionary with query results
        """
        # Search index
        results = self.index_searcher.search(question)

        # Read relevant pages
        contexts = []
        for page_id in results:
            try:
                content = self.page_reader.read(page_id)
                contexts.append(content)
            except FileNotFoundError:
                continue

        return {
            "question": question,
            "results_count": len(results),
            "contexts": contexts
        }

    def lint(self) -> dict:
        """
        Lint the wiki

        Returns:
            Lint report dictionary
        """
        report = lint_wiki()

        return {
            "total_pages": report.total_pages,
            "issues_found": report.issues_found,
            "issues_fixed": report.issues_fixed,
            "recommendations": report.recommendations
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_orchestrator.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_orchestrator.py src/orchestrator.py
git commit -m "feat: implement main orchestrator with ingest/query/lint API"
```

---

### Day 20: Documentation and Deployment

#### Task 4.3: Create configuration and documentation

**Files:**
- Modify: `config/schema.yaml`
- Create: `README_4.0.md`

- [ ] **Step 1: Write configuration file**

Modify: `config/schema.yaml`:
```yaml
# KnowledgeMiner 4.0 Wiki Schema

wiki:
  structure:
    index: "wiki/index.md"
    log: "wiki/log.md"
    directories:
      entities: "wiki/entities/"
      concepts: "wiki/concepts/"
      sources: "wiki/sources/"
      synthesis: "wiki/synthesis/"
      comparisons: "wiki/comparisons/"

  conventions:
    naming: "kebab-case"
    links: "wikilink"
    frontmatter: true

  quality:
    min_confidence: 0.6
    max_concepts_per_source: 50
    min_sources_per_concept: 2

raw:
  categories:
    - papers
    - articles
    - reports
    - notes

  conventions:
    encoding: "utf-8"
    line_ending: "lf"
    require_frontmatter: true

enhanced:
  embeddings:
    model: "text-embedding-3-small"
    dimension: 1536
    cache_enabled: true

  discovery:
    patterns:
      enabled: true
      confidence_threshold: 0.7
    gaps:
      enabled: true
      severity_threshold: 0.5
    insights:
      enabled: true
      significance_threshold: 0.6

operations:
  ingest:
    batch_size: 10
    parallel_workers: 3

  query:
    max_results: 10
    context_window: 5

  lint:
    auto_fix: true
    check_interval: "daily"
```

- [ ] **Step 2: Create README**

Create: `README_4.0.md`:
```markdown
# KnowledgeMiner 4.0

## Overview

KnowledgeMiner 4.0 is a complete rewrite based on the LLM Wiki pattern. It provides a three-layer architecture for knowledge management with persistent wiki storage.

## Architecture

```
Raw Sources → Enhanced Models → Wiki Models
  (input)      (processing)      (storage)
```

## Quick Start

### Ingest a Source

```python
from src.orchestrator import KnowledgeMinerOrchestrator

orchestrator = KnowledgeMinerOrchestrator()
result = orchestrator.ingest("raw/papers/paper.md")

print(f"Extracted {result['concepts_extracted']} concepts")
print(f"Created wiki page: {result['wiki_page']}")
```

### Query the Wiki

```python
result = orchestrator.query("machine learning")

print(f"Found {result['results_count']} relevant pages")
for context in result['contexts']:
    print(context)
```

### Lint the Wiki

```python
report = orchestrator.lint()

print(f"Checked {report['total_pages']} pages")
print(f"Found {report['issues_found']} issues")
print(f"Fixed {report['issues_fixed']} issues")
```

## Project Structure

```
KnowledgeMiner/
├── raw/              # Immutable source documents
├── wiki/             # LLM-maintained markdown wiki
├── src/              # Source code
│   ├── raw/          # Source loading and parsing
│   ├── enhanced/     # Enhanced models and processing
│   ├── wiki/         # Wiki models and operations
│   └── orchestrator.py
├── tests/            # Test suite
└── config/           # Configuration files
```

## Development

Run tests:
```bash
pytest tests/ -v
```

Migrate from old system:
```bash
python scripts/migrate_sources.py
python scripts/rebuild_wiki.py
```
```

- [ ] **Step 3: Commit**

```bash
git add config/schema.yaml README_4.0.md
git commit -m "docs: add configuration and 4.0 documentation"
```

---

## Final Steps

### Task 4.4: Run full test suite and validation

- [ ] **Step 1: Run all tests**

Run:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

Expected: All tests pass with >85% coverage

- [ ] **Step 2: Check code quality**

Run:
```bash
pylint src/ --fail-under=8.0
```

Expected: Code quality score > 8.0

- [ ] **Step 3: Run integration tests**

Run:
```bash
pytest tests/test_integration/ -v
```

Expected: All integration tests pass

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete KnowledgeMiner 4.0 implementation

- Implemented three-layer architecture (Raw → Enhanced → Wiki)
- Core operations: ingest, query, lint
- Full test coverage with integration tests
- Migration scripts included
- Configuration and documentation complete

Ready for testing and deployment"
```

---

## Summary

This implementation plan provides:

✅ **Complete 4-week timeline** broken into daily tasks
✅ **Detailed code examples** for every component
✅ **Test-driven development** with tests written first
✅ **Clear file structure** and organization
✅ **Frequent commits** for progress tracking
✅ **Integration tests** for end-to-end validation
✅ **Migration path** from old system
✅ **Documentation** for users and developers

**Next Steps:**
1. Choose execution method (subagent-driven or inline)
2. Begin implementation starting with Week 1, Day 1
3. Track progress using checkbox syntax
4. Run tests frequently to catch issues early
