import pytest
from unittest.mock import Mock, patch, MagicMock
from src.config import Config
from src.main import KnowledgeCompiler
from src.models.concept import Concept, ConceptType


class TestCLIInteraction:
    def setup_method(self):
        self.compiler = KnowledgeCompiler()

    def test_confirm_concepts_no_concepts(self):
        """Test confirm_concepts with no concepts."""
        concepts = []
        confirmed = self.compiler.confirm_concepts(concepts)
        assert confirmed == []

    def test_confirm_concepts_all_confirmed(self):
        """Test confirm_concepts when all concepts are confirmed."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Programming language"
        concept1.type = ConceptType.TERM
        concept1.related_concepts = []

        concept2 = Mock(spec=Concept)
        concept2.name = "Machine Learning"
        concept2.definition = "AI subset"
        concept2.type = ConceptType.THEORY
        concept2.related_concepts = []

        concepts = [concept1, concept2]

        with patch('builtins.input', side_effect=['y', 'y']):
            confirmed = self.compiler.confirm_concepts(concepts)
            assert len(confirmed) == 2
            assert concept1 in confirmed
            assert concept2 in confirmed

    def test_confirm_concepts_partial_confirmation(self):
        """Test confirm_concepts with partial confirmation."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Programming language"
        concept1.type = ConceptType.TERM
        concept1.related_concepts = []

        concept2 = Mock(spec=Concept)
        concept2.name = "Machine Learning"
        concept2.definition = "AI subset"
        concept2.type = ConceptType.THEORY
        concept2.related_concepts = []

        concepts = [concept1, concept2]

        with patch('builtins.input', side_effect=['y', 'n']):
            confirmed = self.compiler.confirm_concepts(concepts)
            assert len(confirmed) == 1
            assert concept1 in confirmed
            assert concept2 not in confirmed

    def test_confirm_concepts_all_rejected(self):
        """Test confirm_concepts when all concepts are rejected."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Programming language"
        concept1.type = ConceptType.TERM
        concept1.related_concepts = []

        concepts = [concept1]

        with patch('builtins.input', side_effect=['n']):
            confirmed = self.compiler.confirm_concepts(concepts)
            assert len(confirmed) == 0

    @patch('src.main.KnowledgeCompiler.confirm_concepts')
    def test_manual_edit_concepts_calls_confirm(self, mock_confirm):
        """Test _manual_edit_concepts calls confirm_concepts."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Programming language"

        concepts = [concept1]
        mock_confirm.return_value = concepts

        result = self.compiler._manual_edit_concepts(concepts)

        mock_confirm.assert_called_once_with(concepts)
        assert result == concepts

    def test_review_concepts_individually_empty(self):
        """Test _review_concepts_individually with empty list."""
        concepts = []
        result = self.compiler._review_concepts_individually(concepts)
        assert result == []

    def test_review_concepts_individually_review_all(self):
        """Test _review_concepts_individually reviewing all concepts."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Original definition"
        concept1.type = ConceptType.TERM
        concept1.related_concepts = []

        concept2 = Mock(spec=Concept)
        concept2.name = "Machine Learning"
        concept2.definition = "Original definition"
        concept2.type = ConceptType.THEORY
        concept2.related_concepts = []

        concepts = [concept1, concept2]

        # Mock input: keep both concepts, continue
        with patch('builtins.input', side_effect=['k', 'k', 'c']):
            with patch('builtins.print') as mock_print:
                result = self.compiler._review_concepts_individually(concepts)

                # Verify all concepts are reviewed
                assert len(result) == 2
                assert concept1 in result
                assert concept2 in result

    def test_review_concepts_individually_skip_some(self):
        """Test _review_concepts_individually skipping some concepts."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Original definition"
        concept1.type = ConceptType.TERM
        concept1.related_concepts = []

        concept2 = Mock(spec=Concept)
        concept2.name = "Machine Learning"
        concept2.definition = "Original definition"
        concept2.type = ConceptType.THEORY
        concept2.related_concepts = []

        concepts = [concept1, concept2]

        # Mock input: keep first, skip second, continue
        with patch('builtins.input', side_effect=['k', 's', 'c']):
            with patch('builtins.print') as mock_print:
                result = self.compiler._review_concepts_individually(concepts)

                # Verify only first concept is included
                assert len(result) == 1
                assert concept1 in result
                assert concept2 not in result

    def test_review_concepts_individually_quit_early(self):
        """Test _review_concepts_individually quitting early."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Original definition"
        concept1.type = ConceptType.TERM
        concept1.related_concepts = []

        concept2 = Mock(spec=Concept)
        concept2.name = "Machine Learning"
        concept2.definition = "Original definition"
        concept2.type = ConceptType.THEORY
        concept2.related_concepts = []

        concepts = [concept1, concept2]

        # Mock input: keep first concept, quit
        with patch('builtins.input', side_effect=['k', 'q']):
            with patch('builtins.print') as mock_print:
                result = self.compiler._review_concepts_individually(concepts)

                # Verify only first concept is included
                assert len(result) == 1
                assert concept1 in result
                assert concept2 not in result

    def test_review_concepts_individually_update_definition(self):
        """Test _review_concepts_individually updating concept definitions."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Original definition"
        concept1.type = ConceptType.TERM
        concept1.related_concepts = []

        concepts = [concept1]

        # Mock input: review, keep, update, new definition, continue
        with patch('builtins.input', side_effect=['y', 'y', 'u', 'Updated definition', 'c']):
            with patch('builtins.print') as mock_print:
                result = self.compiler._review_concepts_individually(concepts)

                # Verify definition was updated
                assert len(result) == 1
                assert result[0].definition == "Updated definition"

    @patch('src.main.KnowledgeCompiler._review_concepts_individually')
    def test_review_concepts_calls_individual_review(self, mock_review):
        """Test review_concepts calls _review_concepts_individually."""
        concept1 = Mock(spec=Concept)
        concept1.name = "Python"
        concept1.definition = "Programming language"

        concepts = [concept1]
        mock_review.return_value = concepts

        result = self.compiler.review_concepts(concepts)

        mock_review.assert_called_once_with(concepts)
        assert result == concepts

    def test_concept_display_format(self):
        """Test concept display format."""
        concept = Mock(spec=Concept)
        concept.name = "Python"
        concept.definition = "A high-level programming language"
        concept.type = ConceptType.TERM
        concept.related_concepts = []

        with patch('builtins.print') as mock_print:
            self.compiler._display_concept(concept)

            # Verify concept is displayed properly
            mock_print.assert_called()
            calls = mock_print.call_args_list
            assert any("Python" in str(call) for call in calls)
            assert any("Term" in str(call) for call in calls)
            assert any("A high-level programming language" in str(call) for call in calls)

    def test_concept_display_format_long_definition(self):
        """Test concept display format with long definition."""
        concept = Mock(spec=Concept)
        concept.name = "Machine Learning"
        concept.definition = "A subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
        concept.type = ConceptType.THEORY
        concept.related_concepts = []

        with patch('builtins.print') as mock_print:
            self.compiler._display_concept(concept)

            # Verify concept is displayed with truncated definition
            calls = mock_print.call_args_list
            assert any("Machine Learning" in str(call) for call in calls)
            assert any("Theory" in str(call) for call in calls)

    def test_interactive_mode_enabled(self):
        """Test behavior when interactive mode is enabled."""
        config = Config()
        config.interactive_mode = True
        config.verbose_output = False

        compiler = KnowledgeCompiler(config)

        # Should enable interactive features
        assert compiler.config.interactive_mode == True

    def test_interactive_mode_disabled(self):
        """Test behavior when interactive mode is disabled."""
        config = Config()
        config.interactive_mode = False
        config.verbose_output = False

        compiler = KnowledgeCompiler(config)

        # Should disable interactive features
        assert compiler.config.interactive_mode == False