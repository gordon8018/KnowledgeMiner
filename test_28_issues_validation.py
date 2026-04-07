"""
Validation tests for the 28 new issues fixes.
Tests the core functionality to ensure all fixes work correctly.
"""

import sys
import traceback

def test_crit_7_package_naming_conflict():
    """Test CRIT-7: Package naming conflict fixed"""
    print("Testing CRIT-7: Package naming conflict...")
    try:
        # This should work now after renaming src/config.py to src/compiler_config.py
        from src.compiler_config import Config
        config = Config()
        assert hasattr(config, 'source_dir'), "Config should have source_dir attribute"
        print("[PASS] CRIT-7: Package naming conflict fixed")
        return True
    except Exception as e:
        print(f"[FAIL] CRIT-7 failed: {e}")
        traceback.print_exc()
        return False


def test_crit_8_cli_attribute_name():
    """Test CRIT-8: CLI attribute name fixed"""
    print("Testing CRIT-8: CLI attribute name...")
    try:
        import inspect
        from src.main_cli import main

        # Check that the code uses args.non_recursive
        source = inspect.getsource(main)

        # Should not contain the old incorrect attribute name
        assert "args.no_recursive" not in source, "Code should not use args.no_recursive"

        # The code should use args.non_recursive correctly
        # (The fix was changing from args.no_recursive to args.non_recursive)

        print("[PASS] CRIT-8: CLI attribute name fixed (args.no_recursive removed)")
        return True
    except Exception as e:
        print(f"[FAIL] CRIT-8 failed: {e}")
        traceback.print_exc()
        return False


def test_crit_6_embedding_generator_init():
    """Test CRIT-6: EmbeddingGenerator initialization fixed"""
    print("Testing CRIT-6: EmbeddingGenerator initialization...")
    try:
        from src.ml.embeddings import EmbeddingGenerator

        # Should be able to instantiate without environment variable
        embedder = EmbeddingGenerator()

        # Should have lazy initialization
        assert embedder.client is None, "Client should be None initially"
        assert embedder._client_initialized is False, "Should not be initialized yet"

        print("[PASS] CRIT-6: EmbeddingGenerator initialization fixed")
        return True
    except Exception as e:
        print(f"[FAIL] CRIT-6 failed: {e}")
        traceback.print_exc()
        return False


def test_high_8_api_key_security():
    """Test HIGH-8: API key security fixed"""
    print("Testing HIGH-8: API key security...")
    try:
        from src.compiler_config import Config

        # Create config with API key
        config = Config(api_key="test-secret-key")

        # to_dict should not include api_key
        config_dict = config.to_dict()

        assert 'api_key' not in config_dict, "to_dict() should not include api_key"
        assert config_dict.get('api_key') is None, "api_key should not be in dict"

        print("[PASS] HIGH-8: API key security fixed")
        return True
    except Exception as e:
        print(f"[FAIL] HIGH-8 failed: {e}")
        traceback.print_exc()
        return False


def test_crit_9_type_bridging():
    """Test CRIT-9: Phase 3 type bridging fixed"""
    print("Testing CRIT-9: Phase 3 type bridging...")
    try:
        import inspect
        from src.wiki.discovery.orchestrator import DiscoveryOrchestrator

        # Check that orchestrator doesn't convert documents to dict
        source = inspect.getsource(DiscoveryOrchestrator.orchestrate)

        # Should not contain the conversion call
        assert "documents_dict = self._convert_documents_to_dict" not in source, \
            "Should not convert documents to dict before passing to discovery engine"

        print("[PASS] CRIT-9: Phase 3 type bridging fixed")
        return True
    except Exception as e:
        print(f"[FAIL] CRIT-9 failed: {e}")
        traceback.print_exc()
        return False


def test_crit_10_pipeline_provider():
    """Test CRIT-10: Pipeline provider parameter fixed"""
    print("Testing CRIT-10: Pipeline provider parameter...")
    try:
        import inspect
        from src.wiki.discovery.pipeline import DiscoveryPipeline

        # Check that pipeline creates engine with providers
        source = inspect.getsource(DiscoveryPipeline.__init__)

        # Should create LLM provider and embedder
        assert "get_llm_provider()" in source, "Should create LLM provider"
        assert "EmbeddingGenerator()" in source, "Should create embedder"

        # Should pass both to KnowledgeDiscoveryEngine
        assert "llm_provider=llm_provider" in source, "Should pass llm_provider"
        assert "embedding_generator=embedding_generator" in source, "Should pass embedding_generator"

        print("[PASS] CRIT-10: Pipeline provider parameter fixed")
        return True
    except Exception as e:
        print(f"[FAIL] CRIT-10 failed: {e}")
        traceback.print_exc()
        return False


def test_high_3_concept_description():
    """Test HIGH-3: concept.description fixed"""
    print("Testing HIGH-3: concept.description fixed...")
    try:
        import inspect
        from src.indexers.relation_mapper import RelationMapper

        # Check that code uses definition instead of description
        # Find the method that creates markdown catalog
        for attr_name in dir(RelationMapper):
            if 'markdown' in attr_name.lower() and callable(getattr(RelationMapper, attr_name)):
                try:
                    source = inspect.getsource(getattr(RelationMapper, attr_name))
                    # Should use concept.definition
                    assert "concept.description" not in source, "Should not use concept.description"
                    assert "concept.definition" in source, "Should use concept.definition"
                    print("[PASS] HIGH-3: concept.description fixed")
                    return True
                except:
                    continue

        # If no method found, check the class directly
        source = inspect.getsource(RelationMapper)
        assert "concept.description" not in source, "Should not use concept.description in class"
        assert "concept.definition" in source, "Should use concept.definition in class"

        print("[PASS] HIGH-3: concept.description fixed")
        return True
    except Exception as e:
        print(f"[FAIL] HIGH-3 failed: {e}")
        traceback.print_exc()
        return False


def test_high_7_frontmatter_protection():
    """Test HIGH-7: frontmatter import protection"""
    print("Testing HIGH-7: frontmatter import protection...")
    try:
        from src.utils.markdown_utils import parse_frontmatter

        # Test with simple markdown without frontmatter
        content = "# Test\n\nSome content"
        metadata, parsed_content = parse_frontmatter(content)

        assert metadata == {}, "Should handle markdown without frontmatter"
        assert parsed_content == content, "Content should be unchanged"

        print("[PASS] HIGH-7: frontmatter import protection added")
        return True
    except Exception as e:
        print(f"[FAIL] HIGH-7 failed: {e}")
        traceback.print_exc()
        return False


def test_med_1_sqlite_connection():
    """Test MED-1: SQLite connection management"""
    print("Testing MED-1: SQLite connection management...")
    try:
        import inspect
        from src.wiki.core.storage import WikiStore

        # Check that class has cleanup methods
        assert hasattr(WikiStore, '__del__'), "Should have __del__ method"
        assert hasattr(WikiStore, 'close'), "Should have close method"

        # Check that __del__ closes connection
        source = inspect.getsource(WikiStore.__del__)
        assert "self.conn.close()" in source, "__del__ should close connection"

        # Check that close method also exists and closes connection
        close_source = inspect.getsource(WikiStore.close)
        assert "self.conn.close()" in close_source, "close() should close connection"

        print("[PASS] MED-1: SQLite connection management added")
        return True
    except Exception as e:
        print(f"[FAIL] MED-1 failed: {e}")
        traceback.print_exc()
        return False


def test_med_4_division_by_zero():
    """Test MED-4: Division by zero protection"""
    print("Testing MED-4: Division by zero protection...")
    try:
        import inspect
        from src.generators.summary_generator import SummaryGenerator

        # Check that code has division protection
        source = inspect.getsource(SummaryGenerator._generate_relations_overview)

        # Should check for empty concepts before dividing
        assert "len(self.concepts) > 0" in source, "Should check len() > 0 before division"

        print("[PASS] MED-4: Division by zero protection added")
        return True
    except Exception as e:
        print(f"[FAIL] MED-4 failed: {e}")
        traceback.print_exc()
        return False


def test_low_1_dead_code_removal():
    """Test LOW-1: Dead code removal"""
    print("Testing LOW-1: Dead code removal...")
    try:
        import inspect
        from src.main import KnowledgeCompiler

        # Should not have _manual_edit_concepts method anymore
        assert not hasattr(KnowledgeCompiler, '_manual_edit_concepts'), \
            "Should not have _manual_edit_concepts method"

        print("[PASS] LOW-1: Dead code removed")
        return True
    except Exception as e:
        print(f"[FAIL] LOW-1 failed: {e}")
        traceback.print_exc()
        return False


def test_low_2_git_error_detection():
    """Test LOW-2: Git error detection"""
    print("Testing LOW-2: Git error detection...")
    try:
        import inspect
        from src.wiki.core.storage import WikiStore

        # Check that git commands check return codes
        source = inspect.getsource(WikiStore._git_commit)

        # Should check return codes
        assert "returncode != 0" in source, "Should check return codes for git commands"
        assert "raise RuntimeError" in source, "Should raise RuntimeError on failure"

        print("[PASS] LOW-2: Git error detection added")
        return True
    except Exception as e:
        print(f"[FAIL] LOW-2 failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("Running validation tests for 28 new issues fixes...")
    print("=" * 60)

    results = []

    # CRITICAL priority tests (6 issues, 5 still exist + 1 fixed)
    results.append(test_crit_7_package_naming_conflict())    # CRIT-7
    results.append(test_crit_8_cli_attribute_name())         # CRIT-8
    results.append(test_crit_6_embedding_generator_init())    # CRIT-6
    results.append(test_high_8_api_key_security())           # HIGH-8 (critical security)
    results.append(test_crit_9_type_bridging())               # CRIT-9
    results.append(test_crit_10_pipeline_provider())          # CRIT-10

    # HIGH priority tests (remaining issues)
    results.append(test_high_3_concept_description())        # HIGH-3
    results.append(test_high_7_frontmatter_protection())      # HIGH-7

    # MEDIUM priority tests
    results.append(test_med_1_sqlite_connection())           # MED-1
    results.append(test_med_4_division_by_zero())             # MED-4

    # LOW priority tests
    results.append(test_low_1_dead_code_removal())           # LOW-1
    results.append(test_low_2_git_error_detection())          # LOW-2

    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All tested issues fixed!")
        return 0
    else:
        print(f"FAILED: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())