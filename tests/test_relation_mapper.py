import pytest
from unittest.mock import Mock
from src.models.document import Document
from src.models.concept import Concept, CandidateConcept
from src.indexers.relation_mapper import RelationMapper


class TestRelationMapper:
    def setup_method(self):
        self.mapper = RelationMapper()

    def test_init(self):
        """Test RelationMapper initialization."""
        assert hasattr(self.mapper, 'documents')
        assert hasattr(self.mapper, 'concepts')
        assert hasattr(self.mapper, 'relations')
        assert isinstance(self.mapper.documents, dict)
        assert isinstance(self.mapper.concepts, dict)
        assert isinstance(self.mapper.relations, dict)

    def test_add_document(self):
        """Test adding a document to the mapper."""
        doc = Mock(spec=Document)
        doc.path = "test.md"
        doc.content = "This is about Python programming."

        self.mapper.add_document(doc)
        assert "test.md" in self.mapper.documents
        assert self.mapper.documents["test.md"] == doc

    def test_add_concept(self):
        """Test adding a concept to the mapper."""
        concept = Mock(spec=Concept)
        concept.name = "Python"
        concept.related_concepts = ["Programming"]

        self.mapper.add_concept(concept)
        assert "Python" in self.mapper.concepts
        assert self.mapper.concepts["Python"] == concept

    def test_add_candidate_concept(self):
        """Test adding a candidate concept to the mapper."""
        candidate = Mock(spec=CandidateConcept)
        candidate.name = "Python"
        candidate.source_file = "test.md"
        candidate.confidence = 0.8

        self.mapper.add_candidate_concept(candidate)
        assert "Python" in self.mapper.candidate_concepts
        assert len(self.mapper.candidate_concepts["Python"]) == 1
        assert candidate in self.mapper.candidate_concepts["Python"]

    def test_add_duplicate_concept(self):
        """Test adding duplicate concept does not replace."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.related_concepts = ["Programming"]

        concept2 = Mock(spec=Concept)
        concept2.name = "Python"
        concept2.related_concepts = ["Coding"]

        self.mapper.add_concept(concept1)
        self.mapper.add_concept(concept2)

        assert "Python" in self.mapper.concepts
        assert self.mapper.concepts["Python"] == concept1  # Should keep first

    def test_add_concept_relation(self):
        """Test adding a relation between concepts."""
        self.mapper.add_concept_relation("Python", "Programming", "parent")
        self.mapper.add_concept_relation("Programming", "Python", "child")

        assert "Python" in self.mapper.relations
        assert "Programming" in self.mapper.relations["Python"]
        assert self.mapper.relations["Python"]["Programming"] == "parent"

        assert "Programming" in self.mapper.relations
        assert "Python" in self.mapper.relations["Programming"]
        assert self.mapper.relations["Programming"]["Python"] == "child"

    def test_add_duplicate_relation(self):
        """Test adding duplicate relation updates the relation type."""
        self.mapper.add_concept_relation("Python", "Programming", "parent")
        self.mapper.add_concept_relation("Python", "Programming", "related")

        assert self.mapper.relations["Python"]["Programming"] == "related"

    def test_get_concept(self):
        """Test retrieving a concept by name."""
        concept = Mock(spec=Concept)
        concept.name = "Python"

        self.mapper.add_concept(concept)
        result = self.mapper.get_concept("Python")
        assert result == concept

    def test_get_concept_not_found(self):
        """Test retrieving non-existent concept."""
        result = self.mapper.get_concept("Nonexistent")
        assert result is None

    def test_get_concept_relations(self):
        """Test getting relations for a concept."""
        self.mapper.add_concept_relation("Python", "Programming", "parent")
        self.mapper.add_concept_relation("Python", "Java", "related")
        self.mapper.add_concept_relation("Python", "C++", "related")

        result = self.mapper.get_concept_relations("Python")
        assert len(result) == 3
        assert result["Programming"] == "parent"
        assert result["Java"] == "related"
        assert result["C++"] == "related"

    def test_get_concept_relations_not_found(self):
        """Test getting relations for non-existent concept."""
        result = self.mapper.get_concept_relations("Nonexistent")
        assert result == {}

    def test_get_concepts_by_relation_type(self):
        """Test getting concepts by relation type."""
        self.mapper.add_concept_relation("Python", "Programming", "parent")
        self.mapper.add_concept_relation("Java", "Programming", "parent")
        self.mapper.add_concept_relation("Python", "Java", "related")

        result = self.mapper.get_concepts_by_relation_type("parent")
        assert len(result) == 2
        assert "Python" in result
        assert "Java" in result

        result = self.mapper.get_concepts_by_relation_type("related")
        assert len(result) == 1
        assert "Python" in result

    def test_get_concepts_by_relation_type_not_found(self):
        """Test getting concepts by non-existent relation type."""
        result = self.mapper.get_concepts_by_relation_type("nonexistent")
        assert result == []

    def test_find_concepts_in_document(self):
        """Test finding concepts in a specific document."""
        candidate1 = Mock(spec=CandidateConcept)
        candidate1.name = "Python"
        candidate1.source_file = "test1.md"
        candidate1.confidence = 0.8

        candidate2 = Mock(spec=CandidateConcept)
        candidate2.name = "Programming"
        candidate2.source_file = "test2.md"
        candidate2.confidence = 0.9

        candidate3 = Mock(spec=CandidateConcept)
        candidate3.name = "Python"
        candidate3.source_file = "test3.md"
        candidate3.confidence = 0.7

        self.mapper.add_candidate_concept(candidate1)
        self.mapper.add_candidate_concept(candidate2)
        self.mapper.add_candidate_concept(candidate3)

        result = self.mapper.find_concepts_in_document("test1.md")
        assert len(result) == 1
        assert result[0] == candidate1

        result = self.mapper.find_concepts_in_document("test2.md")
        assert len(result) == 1
        assert result[0] == candidate2

    def test_find_concepts_in_document_not_found(self):
        """Test finding concepts in non-existent document."""
        result = self.mapper.find_concepts_in_document("nonexistent.md")
        assert result == []

    def test_get_concept_occurrence_count(self):
        """Test getting occurrence count for a concept."""
        candidate1 = Mock(spec=CandidateConcept)
        candidate1.name = "Python"
        candidate1.source_file = "test1.md"

        candidate2 = Mock(spec=CandidateConcept)
        candidate2.name = "Python"
        candidate2.source_file = "test2.md"

        candidate3 = Mock(spec=CandidateConcept)
        candidate3.name = "Python"
        candidate3.source_file = "test3.md"

        self.mapper.add_candidate_concept(candidate1)
        self.mapper.add_candidate_concept(candidate2)
        self.mapper.add_candidate_concept(candidate3)

        assert self.mapper.get_concept_occurrence_count("Python") == 3

    def test_get_concept_occurrence_count_not_found(self):
        """Test getting occurrence count for non-existent concept."""
        assert self.mapper.get_concept_occurrence_count("Nonexistent") == 0

    def test_get_related_concepts(self):
        """Test getting related concepts."""
        self.mapper.add_concept_relation("Python", "Programming", "parent")
        self.mapper.add_concept_relation("Python", "Java", "related")
        self.mapper.add_concept_relation("Programming", "Algorithms", "related")

        result = self.mapper.get_related_concepts("Python", "parent")
        assert result == ["Programming"]

        result = self.mapper.get_related_concepts("Python", "related")
        assert set(result) == {"Java"}

        result = self.mapper.get_related_concepts("Programming", "related")
        assert result == ["Algorithms"]

    def test_get_related_concepts_not_found(self):
        """Test getting related concepts for non-existent concept or relation."""
        result = self.mapper.get_related_concepts("Nonexistent", "parent")
        assert result == []

        result = self.mapper.get_related_concepts("Python", "nonexistent")
        assert result == []

    def remove_concept(self):
        """Test removing a concept."""
        concept = Mock(spec=Concept)
        concept.name = "Python"

        self.mapper.add_concept(concept)
        assert "Python" in self.mapper.concepts

        result = self.mapper.remove_concept("Python")
        assert result == True
        assert "Python" not in self.mapper.concepts

    def test_remove_concept_not_found(self):
        """Test removing non-existent concept."""
        result = self.mapper.remove_concept("Nonexistent")
        assert result == False

    def test_clear_concept_relations(self):
        """Test clearing concept relations."""
        self.mapper.add_concept_relation("Python", "Programming", "parent")
        self.mapper.add_concept_relation("Java", "Programming", "parent")

        self.mapper.clear_concept_relations("Python")
        assert "Python" not in self.mapper.relations
        assert "Java" in self.mapper.relations  # Should keep Java's relations

    def test_clear_concept_relations_not_found(self):
        """Test clearing relations for non-existent concept."""
        self.mapper.clear_concept_relations("Nonexistent")
        assert len(self.mapper.relations) == 0

    def test_get_concept_sources(self):
        """Test getting source documents for a concept."""
        candidate1 = Mock(spec=CandidateConcept)
        candidate1.name = "Python"
        candidate1.source_file = "test1.md"

        candidate2 = Mock(spec=CandidateConcept)
        candidate2.name = "Python"
        candidate2.source_file = "test2.md"

        self.mapper.add_candidate_concept(candidate1)
        self.mapper.add_candidate_concept(candidate2)

        result = self.mapper.get_concept_sources("Python")
        assert set(result) == {"test1.md", "test2.md"}

    def test_get_concept_sources_not_found(self):
        """Test getting sources for non-existent concept."""
        result = self.mapper.get_concept_sources("Nonexistent")
        assert result == []

    def test_get_all_concept_names(self):
        """Test getting all concept names."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"

        concept2 = Mock(spec=Concept)
        concept2.name = "Programming"

        self.mapper.add_concept(concept1)
        self.mapper.add_concept(concept2)

        result = self.mapper.get_all_concept_names()
        assert set(result) == {"Python", "Programming"}

    def test_get_relation_statistics(self):
        """Test getting relation statistics."""
        self.mapper.add_concept_relation("Python", "Programming", "parent")
        self.mapper.add_concept_relation("Python", "Java", "related")
        self.mapper.add_concept_relation("Java", "Programming", "parent")

        result = self.mapper.get_relation_statistics()
        assert result["parent"] == 2
        assert result["related"] == 1

    def test_get_relation_statistics_empty(self):
        """Test getting relation statistics when no relations exist."""
        result = self.mapper.get_relation_statistics()
        assert result == {}

    def test_find_concept_by_similarity(self):
        """Test finding concept by name similarity."""
        # Add actual concepts to make them findable
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept2 = Mock(spec=Concept)
        concept2.name = "Programming"

        self.mapper.add_concept(concept1)
        self.mapper.add_concept(concept2)

        result = self.mapper.find_concept_by_similarity("Pyth")
        assert result == "Python"

        result = self.mapper.find_concept_by_similarity("Program")
        assert result == "Programming"

    def test_find_concept_by_similarity_not_found(self):
        """Test finding concept by similarity when no match found."""
        result = self.mapper.find_concept_by_similarity("Nonexistent")
        assert result is None

    def test_map_relations(self):
        """Test mapping relationships between concepts."""
        # Create mock documents
        doc1 = Mock(spec=Document)
        doc1.path = "test1.md"
        doc1.content = "Python programming and algorithms"

        doc2 = Mock(spec=Document)
        doc2.path = "test2.md"
        doc2.content = "Java programming and data structures"

        # Create mock concepts
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.related_concepts = ["Programming", "Algorithms"]
        concept1.description = "A programming language"

        concept2 = Mock(spec=Concept)
        concept2.name = "Programming"
        concept2.related_concepts = ["Algorithms"]
        concept2.description = "Computer programming"

        concept3 = Mock(spec=Concept)
        concept3.name = "Java"
        concept3.related_concepts = ["Programming"]
        concept3.description = "Another programming language"

        # Create candidate concepts that appear in documents
        candidate1 = Mock(spec=CandidateConcept)
        candidate1.name = "Python"
        candidate1.source_file = "test1.md"

        candidate2 = Mock(spec=CandidateConcept)
        candidate2.name = "Programming"
        candidate2.source_file = "test1.md"

        candidate3 = Mock(spec=CandidateConcept)
        candidate3.name = "Algorithms"
        candidate3.source_file = "test1.md"

        candidate4 = Mock(spec=CandidateConcept)
        candidate4.name = "Java"
        candidate4.source_file = "test2.md"

        candidate5 = Mock(spec=CandidateConcept)
        candidate5.name = "Programming"
        candidate5.source_file = "test2.md"

        # Set up mapper with concepts and candidates
        self.mapper.add_concept(concept1)
        self.mapper.add_concept(concept2)
        self.mapper.add_concept(concept3)
        self.mapper.add_candidate_concept(candidate1)
        self.mapper.add_candidate_concept(candidate2)
        self.mapper.add_candidate_concept(candidate3)
        self.mapper.add_candidate_concept(candidate4)
        self.mapper.add_candidate_concept(candidate5)

        # Map relations
        self.mapper.map_relations([doc1, doc2], [concept1, concept2, concept3])

        # Check that relations were created
        assert len(self.mapper.relations) > 0

        # Check specific relations based on document co-occurrence
        python_relations = self.mapper.get_concept_relations("Python")
        assert "Programming" in python_relations

        java_relations = self.mapper.get_concept_relations("Java")
        assert "Programming" in java_relations

    def test_map_relations_empty_inputs(self):
        """Test mapping relations with empty inputs."""
        self.mapper.map_relations([], [])
        assert len(self.mapper.relations) == 0

    def test_generate_markdown(self):
        """Test generating markdown output."""
        # Set up test data
        concept = Mock(spec=Concept)
        concept.name = "Python"
        concept.definition = "A programming language"
        concept.related_concepts = ["Programming"]

        self.mapper.add_concept(concept)

        # Add some relations
        self.mapper.add_concept_relation("Python", "Programming", "related")

        # Add a candidate concept
        candidate = Mock(spec=CandidateConcept)
        candidate.name = "Python"
        candidate.source_file = "test.md"
        self.mapper.add_candidate_concept(candidate)

        # Generate markdown
        markdown = self.mapper.generate_markdown()

        # Check key content
        assert "# Concept Relationship Map" in markdown
        assert "## Summary" in markdown
        assert "## Concept Details" in markdown
        assert "### Python" in markdown
        assert "Python" in markdown
        assert "Programming" in markdown

    def test_generate_markdown_without_mermaid(self):
        """Test generating markdown without mermaid graphs."""
        # Set up test data
        concept = Mock(spec=Concept)
        concept.name = "Python"
        concept.definition = "A programming language"

        self.mapper.add_concept(concept)
        self.mapper.add_concept_relation("Python", "Programming", "related")

        # Generate markdown without mermaid
        markdown = self.mapper.generate_markdown(include_mermaid=False)

        # Check that mermaid is not present
        assert "```mermaid" not in markdown
        assert "graph TD" not in markdown
        # But content should still be there
        assert "# Concept Relationship Map" in markdown

    def test_generate_markdown_empty_relations(self):
        """Test generating markdown with no relations."""
        # Add a concept with no relations
        concept = Mock(spec=Concept)
        concept.name = "Python"
        concept.definition = "A programming language"

        self.mapper.add_concept(concept)

        # Generate markdown
        markdown = self.mapper.generate_markdown()

        # Should still have content but no mermaid graph
        assert "# Concept Relationship Map" in markdown
        assert "```mermaid" not in markdown

    def test_generate_markdown_save_to_file(self, tmp_path):
        """Test saving markdown to file."""
        import os

        # Set up test data
        concept = Mock(spec=Concept)
        concept.name = "Python"
        concept.definition = "A programming language"

        self.mapper.add_concept(concept)
        self.mapper.add_concept_relation("Python", "Programming", "related")

        # Generate and save markdown
        output_path = tmp_path / "test_markdown.md"
        result = self.mapper.generate_markdown(output_path=str(output_path))

        # Check file was created and has content
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            content = f.read()
            assert "# Concept Relationship Map" in content
            assert "Python" in content

    def test_generate_markdown_with_parent_child_relations(self):
        """Test generating markdown with parent-child relations."""
        # Set up concepts with hierarchical relationships
        concept1 = Mock(spec=Concept)
        concept1.name = "Programming"
        concept1.description = "General programming"

        concept2 = Mock(spec=Concept)
        concept2.name = "Python"
        concept2.description = "Python programming language"

        self.mapper.add_concept(concept1)
        self.mapper.add_concept(concept2)

        # Add parent-child relation
        self.mapper.add_concept_relation("Programming", "Python", "parent")

        # Generate markdown
        markdown = self.mapper.generate_markdown()

        # Check that parent-child relation is documented
        assert "### Programming" in markdown
        assert "### Python" in markdown