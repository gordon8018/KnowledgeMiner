import pytest
from src.models.concept import Concept, ConceptType
from src.generators.backlink_generator import BacklinkGenerator


class TestBacklinkGenerator:
    """Test cases for BacklinkGenerator class."""

    def test_init_generator(self):
        """Test that BacklinkGenerator initializes correctly."""
        generator = BacklinkGenerator()
        assert generator is not None

    def test_generate_backlinks_empty_concepts(self):
        """Test generating backlinks with empty concepts list."""
        generator = BacklinkGenerator()
        concepts = []
        backlinks = generator.generate_backlinks(concepts)

        assert isinstance(backlinks, dict)
        assert len(backlinks) == 0

    def test_generate_backlinks_single_concept(self):
        """Test generating backlinks with single concept."""
        generator = BacklinkGenerator()

        concept = Concept(
            name="Machine Learning",
            type=ConceptType.TERM,
            definition="A subset of AI",
            criteria="Technology",
            applications=[],
            cases=[],
            formulas=[],
            related_concepts=["Artificial Intelligence", "Data Science"],
            backlinks=[]
        )

        backlinks = generator.generate_backlinks([concept])

        assert isinstance(backlinks, dict)
        assert len(backlinks) == 1
        assert "Machine Learning" in backlinks
        assert set(backlinks["Machine Learning"]) == {"Artificial Intelligence", "Data Science"}

    def test_generate_backlinks_multiple_concepts(self):
        """Test generating backlinks with multiple concepts."""
        generator = BacklinkGenerator()

        concepts = [
            Concept(
                name="Machine Learning",
                type=ConceptType.TERM,
                definition="A subset of AI",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Artificial Intelligence", "Data Science"],
                backlinks=[]
            ),
            Concept(
                name="Deep Learning",
                type=ConceptType.TERM,
                definition="Subfield of ML",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Machine Learning", "Neural Networks"],
                backlinks=[]
            ),
            Concept(
                name="Neural Networks",
                type=ConceptType.TERM,
                definition="Computational models",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Deep Learning", "Machine Learning"],
                backlinks=[]
            )
        ]

        backlinks = generator.generate_backlinks(concepts)

        assert isinstance(backlinks, dict)
        assert len(backlinks) == 3

        # Check Machine Learning backlinks
        assert "Machine Learning" in backlinks
        assert set(backlinks["Machine Learning"]) == {"Artificial Intelligence", "Data Science"}

        # Check Deep Learning backlinks
        assert "Deep Learning" in backlinks
        assert set(backlinks["Deep Learning"]) == {"Machine Learning", "Neural Networks"}

        # Check Neural Networks backlinks
        assert "Neural Networks" in backlinks
        assert set(backlinks["Neural Networks"]) == {"Deep Learning", "Machine Learning"}

    def test_generate_relationship_map_empty_concepts(self):
        """Test generating relationship map with empty concepts list."""
        generator = BacklinkGenerator()
        concepts = []
        relationship_map = generator.generate_relationship_map(concepts)

        assert isinstance(relationship_map, dict)
        assert len(relationship_map) == 0

    def test_generate_relationship_map_multiple_concepts(self):
        """Test generating relationship map with multiple concepts."""
        generator = BacklinkGenerator()

        concepts = [
            Concept(
                name="Machine Learning",
                type=ConceptType.TERM,
                definition="A subset of AI",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Artificial Intelligence"],
                backlinks=[]
            ),
            Concept(
                name="Artificial Intelligence",
                type=ConceptType.TERM,
                definition="Intelligent machines",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Machine Learning", "Computer Science"],
                backlinks=[]
            )
        ]

        relationship_map = generator.generate_relationship_map(concepts)

        assert isinstance(relationship_map, dict)
        assert len(relationship_map) == 2

        # Check the relationship map matches backlinks
        assert relationship_map == generator.generate_backlinks(concepts)

    def test_generate_method_exists(self):
        """Test that generate method exists and works correctly."""
        generator = BacklinkGenerator()

        # Test with empty concepts
        result = generator.generate([])
        assert isinstance(result, dict)
        assert len(result) == 0

        # Test with actual concepts
        concept = Concept(
            name="Machine Learning",
            type=ConceptType.TERM,
            definition="A subset of AI",
            criteria="Technology",
            applications=[],
            cases=[],
            formulas=[],
            related_concepts=["Artificial Intelligence"],
            backlinks=[]
        )

        result = generator.generate([concept])
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "Machine Learning" in result

    def test_generate_all_method_exists(self):
        """Test that generate_all method exists and works correctly."""
        generator = BacklinkGenerator()

        # Test with empty concepts
        result = generator.generate_all([])
        assert isinstance(result, dict)
        assert len(result) == 3  # backlinks, relationship_map, summary
        assert 'backlinks' in result
        assert 'relationship_map' in result
        assert 'summary' in result

        # Test with actual concepts
        concept = Concept(
            name="Machine Learning",
            type=ConceptType.TERM,
            definition="A subset of AI",
            criteria="Technology",
            applications=[],
            cases=[],
            formulas=[],
            related_concepts=["Artificial Intelligence"],
            backlinks=[]
        )

        result = generator.generate_all([concept])
        assert isinstance(result, dict)
        assert len(result) == 3
        assert 'backlinks' in result
        assert 'relationship_map' in result
        assert 'summary' in result

        # Check summary content
        summary = result['summary']
        assert summary['total_concepts'] == 1
        assert summary['total_relationships'] == 1
        assert summary['avg_relationships_per_concept'] == 1.0

    def test_generate_backlinks_with_duplicate_relations(self):
        """Test generating backlinks with duplicate related concepts."""
        generator = BacklinkGenerator()

        concept = Concept(
            name="Machine Learning",
            type=ConceptType.TERM,
            definition="A subset of AI",
            criteria="Technology",
            applications=[],
            cases=[],
            formulas=[],
            related_concepts=["Artificial Intelligence", "Data Science", "Artificial Intelligence"],  # Duplicate
            backlinks=[]
        )

        backlinks = generator.generate_backlinks([concept])

        assert isinstance(backlinks, dict)
        assert "Machine Learning" in backlinks
        # Should remove duplicates
        assert len(backlinks["Machine Learning"]) == 2
        assert set(backlinks["Machine Learning"]) == {"Artificial Intelligence", "Data Science"}

    def test_generate_backlinks_with_empty_relations(self):
        """Test generating backlinks with concepts that have no relations."""
        generator = BacklinkGenerator()

        concept = Concept(
            name="Machine Learning",
            type=ConceptType.TERM,
            definition="A subset of AI",
            criteria="Technology",
            applications=[],
            cases=[],
            formulas=[],
            related_concepts=[],  # No relations
            backlinks=[]
        )

        backlinks = generator.generate_backlinks([concept])

        assert isinstance(backlinks, dict)
        assert "Machine Learning" in backlinks
        assert len(backlinks["Machine Learning"]) == 0

    def test_generate_relationship_map_complex_relationships(self):
        """Test generating relationship map with complex relationships."""
        generator = BacklinkGenerator()

        concepts = [
            Concept(
                name="Machine Learning",
                type=ConceptType.TERM,
                definition="A subset of AI",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Artificial Intelligence", "Statistics", "Data Science"],
                backlinks=[]
            ),
            Concept(
                name="Deep Learning",
                type=ConceptType.TERM,
                definition="Subfield of ML",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Machine Learning", "Neural Networks", "Computer Vision"],
                backlinks=[]
            ),
            Concept(
                name="Reinforcement Learning",
                type=ConceptType.TERM,
                definition="Learning through rewards",
                criteria="Technology",
                applications=[],
                cases=[],
                formulas=[],
                related_concepts=["Machine Learning", "Game Theory"],
                backlinks=[]
            )
        ]

        relationship_map = generator.generate_relationship_map(concepts)

        assert isinstance(relationship_map, dict)
        assert len(relationship_map) == 3

        # Verify all relationships are captured correctly
        assert relationship_map["Machine Learning"] == ["Artificial Intelligence", "Statistics", "Data Science"]
        assert relationship_map["Deep Learning"] == ["Machine Learning", "Neural Networks", "Computer Vision"]
        assert relationship_map["Reinforcement Learning"] == ["Machine Learning", "Game Theory"]