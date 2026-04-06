# tests/test_models.py
import pytest
from datetime import datetime
from src.models.document import Document, Section
from src.models.concept import Concept, ConceptType

def test_section_creation():
    section = Section(title="Introduction", level=1, content="Test content")
    assert section.title == "Introduction"
    assert section.level == 1
    assert section.content == "Test content"

def test_document_creation():
    doc = Document(
        path="test.md",
        hash="abc123",
        metadata={"title": "Test", "tags": ["test"]},
        sections=[],
        content="# Test\n\nContent"
    )
    assert doc.path == "test.md"
    assert doc.hash == "abc123"
    assert doc.metadata["title"] == "Test"

def test_document_properties():
    doc = Document(
        path="test.md",
        hash="abc123",
        metadata={"title": "Test Title", "tags": ["tag1", "tag2"]},
        sections=[],
        content="# Test\n\nContent"
    )
    assert doc.title == "Test Title"
    assert doc.tags == ["tag1", "tag2"]
    assert doc.title == doc.metadata.get("title")

def test_concept_type_enum():
    assert ConceptType.TERM.value == "term"
    assert ConceptType.INDICATOR.value == "indicator"
    assert ConceptType.STRATEGY.value == "strategy"
    assert ConceptType.THEORY.value == "theory"
    assert ConceptType.PERSON.value == "person"

def test_candidate_concept_creation():
    from src.models.concept import CandidateConcept
    concept = CandidateConcept(
        name="测试概念",
        type=ConceptType.TERM,
        confidence=0.85,
        context="测试上下文",
        source_section="测试章节",
        source_file="test.md"
    )
    assert concept.name == "测试概念"
    assert concept.type == ConceptType.TERM
    assert concept.confidence == 0.85

def test_concept_creation():
    concept = Concept(
        name="测试概念",
        type=ConceptType.TERM,
        definition="测试定义",
        criteria="测试标准",
        applications=[],
        cases=[],
        formulas=[],
        related_concepts=[],
        backlinks=[]
    )
    assert concept.name == "测试概念"
    assert concept.definition == "测试定义"