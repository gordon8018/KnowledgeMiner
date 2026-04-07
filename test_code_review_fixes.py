"""
Validation tests for code review fixes (Post-commit b789caf).
Tests all the fixes for issues discovered during code review.
"""

import sys
import traceback


def test_new_1_generate_embeddings_ensure_client():
    """Test NEW #1: generate_embeddings() calls _ensure_client()"""
    print("Testing NEW #1: generate_embeddings() _ensure_client() call...")
    try:
        import inspect
        from src.ml.embeddings import EmbeddingGenerator

        # Check that generate_embeddings calls _ensure_client
        source = inspect.getsource(EmbeddingGenerator.generate_embeddings)

        # Should have _ensure_client call
        assert "_ensure_client()" in source, \
            "generate_embeddings() must call _ensure_client() before using self.client"

        print("[PASS] NEW #1: generate_embeddings() calls _ensure_client()")
        return True
    except Exception as e:
        print(f"[FAIL] NEW #1 failed: {e}")
        traceback.print_exc()
        return False


def test_new_2_delete_page_file_list():
    """Test NEW #2: delete_page() passes file list not empty list"""
    print("Testing NEW #2: delete_page() file list parameter...")
    try:
        import inspect
        from src.wiki.core.storage import WikiStore

        # Check that delete_page doesn't pass empty list
        source = inspect.getsource(WikiStore.delete_page)

        # Should not have the old empty list call
        assert '_git_commit(f"Delete page: {page_id}", [])' not in source, \
            "delete_page() should not pass empty list to _git_commit()"

        # Should pass actual file path
        assert "relative_path" in source, \
            "delete_page() should calculate and pass relative_path"
        assert "[relative_path]" in source, \
            "delete_page() should pass [relative_path] to _git_commit()"

        print("[PASS] NEW #2: delete_page() passes file path list")
        return True
    except Exception as e:
        print(f"[FAIL] NEW #2 failed: {e}")
        traceback.print_exc()
        return False


def test_crit_6_batch_with_retry_ensure_client():
    """Test CRIT-6: _generate_batch_with_retry() calls _ensure_client()"""
    print("Testing CRIT-6: _generate_batch_with_retry() _ensure_client() call...")
    try:
        import inspect
        from src.ml.embeddings import EmbeddingGenerator

        # Check that _generate_batch_with_retry calls _ensure_client
        source = inspect.getsource(EmbeddingGenerator._generate_batch_with_retry)

        # Should have _ensure_client call
        assert "_ensure_client()" in source, \
            "_generate_batch_with_retry() must call _ensure_client() for defensive programming"

        print("[PASS] CRIT-6: _generate_batch_with_retry() calls _ensure_client()")
        return True
    except Exception as e:
        print(f"[FAIL] CRIT-6 failed: {e}")
        traceback.print_exc()
        return False


def test_new_3_db_git_transaction_order():
    """Test NEW #3: DB and Git transaction order"""
    print("Testing NEW #3: DB and Git transaction order...")
    try:
        import inspect
        from src.wiki.core.storage import WikiStore

        # Check create_page order
        create_source = inspect.getsource(WikiStore.create_page)
        assert create_source.index("_git_commit") < create_source.index("conn.execute"), \
            "create_page() should call _git_commit() before conn.execute()"

        # Check update_page order
        update_source = inspect.getsource(WikiStore.update_page)
        assert update_source.index("_git_commit") < update_source.index("conn.execute"), \
            "update_page() should call _git_commit() before conn.execute()"

        # Check delete_page order
        delete_source = inspect.getsource(WikiStore.delete_page)
        assert delete_source.index("_git_commit") < delete_source.index("conn.execute"), \
            "delete_page() should call _git_commit() before conn.execute()"

        print("[PASS] NEW #3: DB and Git transaction order fixed")
        return True
    except Exception as e:
        print(f"[FAIL] NEW #3 failed: {e}")
        traceback.print_exc()
        return False


def test_high_process_line_removed():
    """Test HIGH: _process_line dead code removed"""
    print("Testing HIGH: _process_line dead code removed...")
    try:
        from src.extractors.concept_extractor import ConceptExtractor

        # Should not have _process_line method anymore
        assert not hasattr(ConceptExtractor, '_process_line'), \
            "_process_line() dead code should be removed"

        print("[PASS] HIGH: _process_line dead code removed")
        return True
    except Exception as e:
        print(f"[FAIL] HIGH failed: {e}")
        traceback.print_exc()
        return False


def test_med_1_context_manager():
    """Test MED-1: WikiStore context manager support"""
    print("Testing MED-1: WikiStore context manager support...")
    try:
        from src.wiki.core.storage import WikiStore

        # Should have __enter__ and __exit__ methods
        assert hasattr(WikiStore, '__enter__'), "Should have __enter__ method"
        assert hasattr(WikiStore, '__exit__'), "Should have __exit__ method"

        # Check __enter__ returns self
        import inspect
        enter_source = inspect.getsource(WikiStore.__enter__)
        assert "return self" in enter_source, "__enter__ should return self"

        # Check __exit__ calls close()
        exit_source = inspect.getsource(WikiStore.__exit__)
        assert "self.close()" in exit_source, "__exit__ should call self.close()"

        print("[PASS] MED-1: WikiStore context manager support added")
        return True
    except Exception as e:
        print(f"[FAIL] MED-1 failed: {e}")
        traceback.print_exc()
        return False


def test_backlink_logger():
    """Test MEDIUM: backlink_generator.py uses logger not print"""
    print("Testing MEDIUM: backlink_generator.py uses logger...")
    try:
        import inspect
        from src.generators.backlink_generator import BacklinkGenerator

        # Check that module has logger
        import src.generators.backlink_generator as bg_module
        assert hasattr(bg_module, 'logger'), "Module should have logger"

        # Check class source doesn't contain print
        source = inspect.getsource(BacklinkGenerator)
        assert "print(" not in source, "Should not use print() statements"

        # Check for logger.warning
        assert "logger.warning" in source, "Should use logger.warning()"

        print("[PASS] MEDIUM: backlink_generator.py uses logger")
        return True
    except Exception as e:
        print(f"[FAIL] MEDIUM (backlink) failed: {e}")
        traceback.print_exc()
        return False


def test_state_manager_context_manager():
    """Test MEDIUM: state_manager.py context manager support"""
    print("Testing MEDIUM: state_manager.py context manager support...")
    try:
        from src.core.state_manager import StateManager

        # Should have __enter__ and __exit__ methods
        assert hasattr(StateManager, '__enter__'), "Should have __enter__ method"
        assert hasattr(StateManager, '__exit__'), "Should have __exit__ method"

        # Check __enter__ returns self
        import inspect
        enter_source = inspect.getsource(StateManager.__enter__)
        assert "return self" in enter_source, "__enter__ should return self"

        # Check __exit__ calls save()
        exit_source = inspect.getsource(StateManager.__exit__)
        assert "self.save()" in exit_source, "__exit__ should call self.save()"

        print("[PASS] MEDIUM: state_manager.py context manager support added")
        return True
    except Exception as e:
        print(f"[FAIL] MEDIUM (state_manager) failed: {e}")
        traceback.print_exc()
        return False


def test_concept_definition_in_tests():
    """Test MEDIUM: tests use concept.definition not concept.description"""
    print("Testing MEDIUM: tests use concept.definition...")
    try:
        with open('tests/test_relation_mapper.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Should not have concept.description
        assert 'concept.description' not in content, \
            "Tests should not use concept.description"

        # Should have concept.definition
        assert 'concept.definition' in content, \
            "Tests should use concept.definition"

        print("[PASS] MEDIUM: tests use concept.definition")
        return True
    except Exception as e:
        print(f"[FAIL] MEDIUM (tests) failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("Running validation tests for code review fixes...")
    print("=" * 60)

    results = []

    # Critical/High priority fixes
    results.append(test_new_1_generate_embeddings_ensure_client())  # NEW #1
    results.append(test_new_2_delete_page_file_list())  # NEW #2
    results.append(test_crit_6_batch_with_retry_ensure_client())  # CRIT-6
    results.append(test_new_3_db_git_transaction_order())  # NEW #3
    results.append(test_high_process_line_removed())  # HIGH

    # Medium priority fixes
    results.append(test_med_1_context_manager())  # MED-1
    results.append(test_backlink_logger())  # MEDIUM (backlink)
    results.append(test_state_manager_context_manager())  # MEDIUM (state_manager)
    results.append(test_concept_definition_in_tests())  # MEDIUM (tests)

    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All code review fixes validated!")
        return 0
    else:
        print(f"FAILED: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
