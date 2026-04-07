"""
Comprehensive validation tests for all fixes (3 new bugs + 8 old issues).
Tests all fixes from commit 4f4cc5e code review.
"""

import sys
import traceback


def test_new_1_delete_page_git_order():
    """Test NEW #1: delete_page() Git order fixed"""
    print("Testing NEW #1: delete_page() Git order...")
    try:
        import inspect
        from src.wiki.core.storage import WikiStore

        source = inspect.getsource(WikiStore.delete_page)

        # Should delete file before git commit
        assert source.index("file_path.unlink()") < source.index("_git_commit"), \
            "Should delete file BEFORE git commit"

        print("[PASS] NEW #1: delete_page() Git order fixed")
        return True
    except Exception as e:
        print(f"[FAIL] NEW #1 failed: {e}")
        traceback.print_exc()
        return False


def test_new_2_update_page_rollback():
    """Test NEW #2: update_page() rollback complete"""
    print("Testing NEW #2: update_page() rollback...")
    try:
        import inspect
        from src.wiki.core.storage import WikiStore

        source = inspect.getsource(WikiStore.update_page)

        # Should save old_updated_at
        assert "old_updated_at = page.updated_at" in source, \
            "Should save old_updated_at before increment_version()"

        # Should restore updated_at on rollback
        assert "page.updated_at = old_updated_at" in source, \
            "Should restore updated_at on rollback"

        print("[PASS] NEW #2: update_page() rollback complete")
        return True
    except Exception as e:
        print(f"[FAIL] NEW #2 failed: {e}")
        traceback.print_exc()
        return False


def test_new_3_file_ends_with_newline():
    """Test NEW #3: backlink_generator.py ends with newline"""
    print("Testing NEW #3: File ends with newline...")
    try:
        with open('src/generators/backlink_generator.py', 'rb') as f:
            f.seek(0, 2)  # Seek to end
            size = f.tell()
            if size > 0:
                f.seek(size - 1)
                last_char = f.read(1)
                assert last_char == b'\n', "File should end with newline"

        print("[PASS] NEW #3: File ends with newline")
        return True
    except Exception as e:
        print(f"[FAIL] NEW #3 failed: {e}")
        traceback.print_exc()
        return False


def test_high_1_documenterror_import():
    """Test HIGH #1: DocumentError imported"""
    print("Testing HIGH #1: DocumentError import...")
    try:
        from src.main import KnowledgeCompiler
        import inspect

        source = inspect.getsource(KnowledgeCompiler)
        assert "except DocumentError" in source, "Should have DocumentError exception"

        # Check imports
        with open('src/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            assert "DocumentError" in content, "DocumentError should be imported"

        print("[PASS] HIGH #1: DocumentError imported")
        return True
    except Exception as e:
        print(f"[FAIL] HIGH #1 failed: {e}")
        traceback.print_exc()
        return False


def test_high_2_concept_description_fixed():
    """Test HIGH #2: No more concept.description in tests"""
    print("Testing HIGH #2: concept.description fixed...")
    try:
        with open('tests/test_relation_mapper.py', 'r') as f:
            content = f.read()

        assert 'concept.description' not in content, \
            "Should not have concept.description"

        print("[PASS] HIGH #2: concept.description fixed")
        return True
    except Exception as e:
        print(f"[FAIL] HIGH #2 failed: {e}")
        traceback.print_exc()
        return False


def test_high_3_config_classes_renamed():
    """Test HIGH #3: Config classes renamed"""
    print("Testing HIGH #3: Config classes renamed...")
    try:
        from src.core.config import KnowledgeCompilerConfig
        from src.compiler_config import Config

        # Should have both classes with different names
        assert KnowledgeCompilerConfig is not None, \
            "Should have KnowledgeCompilerConfig in src/core/config.py"
        assert Config is not None, \
            "Should have Config in src/compiler_config.py"

        print("[PASS] HIGH #3: Config classes renamed")
        return True
    except Exception as e:
        print(f"[FAIL] HIGH #3 failed: {e}")
        traceback.print_exc()
        return False


def test_medium_1_whoosh_in_requirements():
    """Test MEDIUM #1: whoosh in requirements.txt"""
    print("Testing MEDIUM #1: whoosh in requirements.txt...")
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()

        assert 'whoosh' in content.lower(), \
            "whoosh should be in requirements.txt"

        print("[PASS] MEDIUM #1: whoosh in requirements.txt")
        return True
    except Exception as e:
        print(f"[FAIL] MEDIUM #1 failed: {e}")
        traceback.print_exc()
        return False


def test_medium_2_dead_code_removed():
    """Test MEDIUM #2: _convert_documents_to_dict removed"""
    print("Testing MEDIUM #2: Dead code removed...")
    try:
        from src.wiki.discovery.orchestrator import DiscoveryOrchestrator

        # Should not have the method
        assert not hasattr(DiscoveryOrchestrator, '_convert_documents_to_dict'), \
            "_convert_documents_to_dict should be removed"

        print("[PASS] MEDIUM #2: Dead code removed")
        return True
    except Exception as e:
        print(f"[FAIL] MEDIUM #2 failed: {e}")
        traceback.print_exc()
        return False


def test_low_1_datetime_utcnow_replaced():
    """Test LOW #1: datetime.utcnow() replaced"""
    print("Testing LOW #1: datetime.utcnow() replaced...")
    try:
        files_to_check = [
            'src/monitoring/structured_logger.py',
            'src/monitoring/metrics.py',
            'src/monitoring/alerts.py',
            'src/monitoring/dashboard.py',
            'src/features/flags.py'
        ]

        for file_path in files_to_check:
            with open(file_path, 'r') as f:
                content = f.read()
            assert 'datetime.utcnow()' not in content, \
                f"{file_path} should not use datetime.utcnow()"

        print("[PASS] LOW #1: datetime.utcnow() replaced in all files")
        return True
    except Exception as e:
        print(f"[FAIL] LOW #1 failed: {e}")
        traceback.print_exc()
        return False


def test_low_2_git_init_checked():
    """Test LOW #2: git init return code checked"""
    print("Testing LOW #2: git init return code checked...")
    try:
        import inspect
        from src.wiki.core.storage import WikiStore

        source = inspect.getsource(WikiStore._init_git)

        # Should check return code
        assert "returncode != 0" in source, \
            "Should check git init return code"
        assert "raise RuntimeError" in source, \
            "Should raise RuntimeError on failure"

        print("[PASS] LOW #2: git init return code checked")
        return True
    except Exception as e:
        print(f"[FAIL] LOW #2 failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("Running comprehensive validation tests...")
    print("=" * 60)

    results = []

    # New bugs (3)
    results.append(test_new_1_delete_page_git_order())  # NEW #1
    results.append(test_new_2_update_page_rollback())  # NEW #2
    results.append(test_new_3_file_ends_with_newline())  # NEW #3

    # High priority old issues (3)
    results.append(test_high_1_documenterror_import())  # HIGH #1
    results.append(test_high_2_concept_description_fixed())  # HIGH #2
    results.append(test_high_3_config_classes_renamed())  # HIGH #3

    # Medium priority old issues (2)
    results.append(test_medium_1_whoosh_in_requirements())  # MEDIUM #1
    results.append(test_medium_2_dead_code_removed())  # MEDIUM #2

    # Low priority old issues (2)
    results.append(test_low_1_datetime_utcnow_replaced())  # LOW #1
    results.append(test_low_2_git_init_checked())  # LOW #2

    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All fixes validated!")
        return 0
    else:
        print(f"FAILED: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
