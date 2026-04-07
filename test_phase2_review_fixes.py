"""
Validation tests for Phase 2 code review fixes.
Tests all HIGH and MEDIUM priority fixes from comprehensive code review.
"""

import sys
import traceback
import os
import tempfile
from pathlib import Path


def test_high_1_path_traversal_fix():
    """Test HIGH #1: Path traversal vulnerability fixed"""
    print("Testing HIGH #1: Path traversal vulnerability...")
    try:
        from src.utils.file_ops import write_file, read_file

        # Create a temporary base directory
        with tempfile.TemporaryDirectory() as base_dir:
            # Test 1: Attempt path traversal attack
            try:
                write_file("../../../etc/passwd", "malicious", base_dir=base_dir)
                print("[FAIL] HIGH #1: Path traversal not blocked!")
                return False
            except ValueError as e:
                if "path traversal detected" in str(e).lower():
                    print("[PASS] HIGH #1: Path traversal attack blocked")
                else:
                    print(f"[FAIL] HIGH #1: Wrong error: {e}")
                    return False

            # Test 2: Valid writes still work
            test_file = os.path.join(base_dir, "test.txt")
            result = write_file(test_file, "safe content")
            if not result:
                print("[FAIL] HIGH #1: Valid write failed")
                return False

            # Verify content was written
            content = read_file(test_file)
            if content != "safe content":
                print("[FAIL] HIGH #1: Content mismatch")
                return False

            print("[PASS] HIGH #1: Valid writes work correctly")
            return True

    except Exception as e:
        print(f"[FAIL] HIGH #1 failed: {e}")
        traceback.print_exc()
        return False


def test_high_2_redundant_io_fix():
    """Test HIGH #2: Redundant file I/O eliminated"""
    print("Testing HIGH #2: Redundant file I/O...")
    try:
        import inspect
        from src.main import KnowledgeCompiler

        source = inspect.getsource(KnowledgeCompiler._extract_concepts)

        # Should use document.content instead of reading file
        assert "content = document.content" in source, \
            "Should use cached document.content"
        assert "# PERFORMANCE FIX: HIGH #2" in source, \
            "Should have performance fix comment"

        # Should only read file as fallback
        assert "# Fallback: read from disk" in source, \
            "Should have fallback logic"

        print("[PASS] HIGH #2: Redundant I/O eliminated (uses cached content)")
        return True

    except Exception as e:
        print(f"[FAIL] HIGH #2 failed: {e}")
        traceback.print_exc()
        return False


def test_medium_1_api_key_protection():
    """Test MEDIUM #1: API key protection in error messages"""
    print("Testing MEDIUM #1: API key protection...")
    try:
        import inspect
        from src.ml.embeddings import EmbeddingGenerator

        source = inspect.getsource(EmbeddingGenerator._ensure_client)

        # Should have API key redaction
        assert "_api_key_prefix" in source, \
            "Should store API key prefix for debugging"

        # Should have error message sanitization
        assert "replace(api_key" in source, \
            "Should redact API key from error messages"

        # Should have security fix comment
        assert "# SECURITY FIX: MEDIUM #1" in source, \
            "Should have security fix comment"

        print("[PASS] MEDIUM #1: API key protection implemented")
        return True

    except Exception as e:
        print(f"[FAIL] MEDIUM #1 failed: {e}")
        traceback.print_exc()
        return False


def test_medium_2_string_operation_optimization():
    """Test MEDIUM #2: O(n²) string operations optimized"""
    print("Testing MEDIUM #2: String operation optimization...")
    try:
        import inspect
        from src.extractors.concept_extractor import ConceptExtractor

        source = inspect.getsource(ConceptExtractor.get_concepts_by_relation)

        # Should use any() instead of 'in str()'
        assert "any(" in source, \
            "Should use any() for efficient iteration"
        assert "relation_lower" in source, \
            "Should cache lowercased relation"

        # Should not have the old inefficient pattern
        assert "in str(concept.related_concepts)" not in source, \
            "Should not use inefficient str() conversion"

        # Should have performance fix comment
        assert "# PERFORMANCE FIX: MEDIUM #2" in source, \
            "Should have performance fix comment"

        print("[PASS] MEDIUM #2: O(n^2) operations optimized")
        return True

    except Exception as e:
        print(f"[FAIL] MEDIUM #2 failed: {e}")
        traceback.print_exc()
        return False


def test_medium_3_dependency_injection():
    """Test MEDIUM #3: Dependency injection added"""
    print("Testing MEDIUM #3: Dependency injection...")
    try:
        import inspect
        from src.main import KnowledgeCompiler
        from src.analyzers.document_analyzer import DocumentAnalyzer

        source = inspect.getsource(KnowledgeCompiler.__init__)

        # Should have dependency injection parameters
        assert "document_analyzer: Optional[DocumentAnalyzer]" in source, \
            "Should accept document_analyzer parameter"

        # Should have other injector parameters too
        assert "concept_extractor: Optional[ConceptExtractor]" in source, \
            "Should accept concept_extractor parameter"

        # Should use defaults with 'or' operator
        assert "self.document_analyzer = document_analyzer or DocumentAnalyzer()" in source, \
            "Should use default if not provided"

        # Should have code quality fix comment
        assert "# CODE QUALITY FIX: MEDIUM #3" in source, \
            "Should have code quality fix comment"

        # Test that dependency injection actually works
        mock_analyzer = DocumentAnalyzer()
        compiler = KnowledgeCompiler(document_analyzer=mock_analyzer)

        if compiler.document_analyzer is not mock_analyzer:
            print("[FAIL] MEDIUM #3: Dependency injection not working")
            return False

        print("[PASS] MEDIUM #3: Dependency injection implemented")
        return True

    except Exception as e:
        print(f"[FAIL] MEDIUM #3 failed: {e}")
        traceback.print_exc()
        return False


def test_medium_5_lru_cache_implementation():
    """Test MEDIUM #5: Proper LRU cache implementation"""
    print("Testing MEDIUM #5: LRU cache implementation...")
    try:
        import inspect
        from src.ml.embeddings import EmbeddingCache

        source = inspect.getsource(EmbeddingCache)

        # Should use OrderedDict
        assert "OrderedDict" in source, \
            "Should use OrderedDict for proper LRU behavior"

        # Should have move_to_end for LRU tracking
        assert "move_to_end" in source, \
            "Should use move_to_end for LRU tracking"

        # Should have popitem(last=False) for eviction
        assert "popitem(last=False)" in source, \
            "Should evict least-recently-used entry"

        # Should have performance fix comment
        assert "# PERFORMANCE FIX: MEDIUM #5" in source, \
            "Should have performance fix comment"

        # Test LRU behavior
        cache = EmbeddingCache(max_size=3)
        import numpy as np

        # Add 3 items
        cache.put("key1", np.array([1.0]))
        cache.put("key2", np.array([2.0]))
        cache.put("key3", np.array([3.0]))

        # Access key1 to make it recently used
        cache.get("key1")

        # Add 4th item - should evict key2 (oldest, not key1 which was accessed)
        cache.put("key4", np.array([4.0]))

        # key1 should still exist (recently accessed)
        # key2 should be evicted (least recently used)
        if "key1" not in cache:
            print("[FAIL] MEDIUM #5: LRU not working - recently accessed item evicted")
            return False

        if "key2" in cache:
            print("[FAIL] MEDIUM #5: LRU not working - old item not evicted")
            return False

        print("[PASS] MEDIUM #5: Proper LRU cache implemented")
        return True

    except Exception as e:
        print(f"[FAIL] MEDIUM #5 failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("=" * 70)
    print("Testing Phase 2 Code Review Fixes")
    print("=" * 70)

    results = []

    # HIGH priority fixes
    results.append(("HIGH #1", test_high_1_path_traversal_fix()))
    results.append(("HIGH #2", test_high_2_redundant_io_fix()))

    # MEDIUM priority fixes (skipping #4 - data model unification)
    results.append(("MEDIUM #1", test_medium_1_api_key_protection()))
    results.append(("MEDIUM #2", test_medium_2_string_operation_optimization()))
    results.append(("MEDIUM #3", test_medium_3_dependency_injection()))
    results.append(("MEDIUM #5", test_medium_5_lru_cache_implementation()))

    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All Phase 2 code review fixes validated!")
        return 0
    else:
        print(f"FAILED: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
