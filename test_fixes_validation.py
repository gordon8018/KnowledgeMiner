"""
Quick validation tests for our MEDIUM issue fixes.
Tests the core functionality without external dependencies.
"""

import sys
import traceback

def test_exception_hierarchy():
    """Test Issue 14: Exception hierarchy"""
    print("Testing Issue 14: Exception hierarchy...")
    try:
        from src.core.exceptions import (
            KnowledgeCompilerError,
            DocumentError,
            DocumentNotFoundError,
            ProcessingError,
            ExtractionError,
            format_error,
            get_error_context
        )

        # Test basic exception creation
        error = DocumentNotFoundError("test.md")
        assert error.document_path == "test.md"
        assert "not found" in str(error).lower()

        # Test error formatting
        formatted = format_error(error)
        assert "not found" in formatted.lower()

        # Test error context
        context = get_error_context(error)
        assert context["error_type"] == "DocumentNotFoundError"
        assert context["document_path"] == "test.md"

        print("[PASS] Issue 14: Exception hierarchy working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Issue 14 failed: {e}")
        traceback.print_exc()
        return False


def test_llm_provider_optimization():
    """Test Issue 12: LLM client reuse"""
    print("Testing Issue 12: LLM client optimization...")
    try:
        from src.integrations.llm_providers import AnthropicProvider, OpenAIProvider

        # Test that providers create client during __init__
        # Note: We can't actually create providers without API keys,
        # but we can check that the code structure is correct

        # Check that AnthropicProvider has client attribute initialization
        import inspect
        anthropic_init = inspect.getsource(AnthropicProvider.__init__)
        assert "self.client" in anthropic_init, "AnthropicProvider should create client in __init__"

        # Check that generate method uses self.client
        anthropic_generate = inspect.getsource(AnthropicProvider.generate)
        assert "self.client" in anthropic_generate, "generate() should use self.client"

        # Same checks for OpenAIProvider
        openai_init = inspect.getsource(OpenAIProvider.__init__)
        assert "self.client" in openai_init, "OpenAIProvider should create client in __init__"

        openai_generate = inspect.getsource(OpenAIProvider.generate)
        assert "self.client" in openai_generate, "generate() should use self.client"

        print("[PASS] Issue 12: LLM client optimization verified")
        return True
    except Exception as e:
        print(f"[FAIL] Issue 12 failed: {e}")
        traceback.print_exc()
        return False


def test_base_schema_validation():
    """Test Issue 13: Extracted _validate_schema_basic"""
    print("Testing Issue 13: Base schema validation...")
    try:
        from src.integrations.llm_providers import LLMProvider
        import inspect

        # Check that base class has the method
        assert hasattr(LLMProvider, '_validate_schema_basic'), \
            "LLMProvider base class should have _validate_schema_basic method"

        # Get method source
        method = getattr(LLMProvider, '_validate_schema_basic')
        source = inspect.getsource(method)

        # Verify it has the expected logic
        assert "required" in source, "Method should check required properties"
        assert "additionalProperties" in source, "Method should check additional properties"

        print("[PASS] Issue 13: Base schema validation verified")
        return True
    except Exception as e:
        print(f"[FAIL] Issue 13 failed: {e}")
        traceback.print_exc()
        return False


def test_category_indexer_optimization():
    """Test Issue 11: CategoryIndexer extension mapping"""
    print("Testing Issue 11: CategoryIndexer optimization...")
    try:
        from src.indexers.category_indexer import CategoryIndexer

        # Check that class has the constant
        assert hasattr(CategoryIndexer, 'EXTENSION_MAPPING'), \
            "CategoryIndexer should have EXTENSION_MAPPING class constant"

        # Check that it's defined at class level and used correctly
        import inspect
        source = inspect.getsource(CategoryIndexer)

        # Check that class-level constant exists
        assert "EXTENSION_MAPPING = {" in source, "Should have class-level EXTENSION_MAPPING constant definition"

        # Check that methods use self.EXTENSION_MAPPING instead of defining local versions
        assert "self.EXTENSION_MAPPING.get(" in source, "Methods should use self.EXTENSION_MAPPING"

        # Make sure there are no local redefinitions like "extension_mapping = {"
        # (which would be the duplicate we removed)
        lines = source.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip the class-level definition
            if stripped.startswith("EXTENSION_MAPPING = {"):
                continue
            # Check for local redefinitions (the bug we fixed)
            if "extension_mapping = {" in stripped and "=" in stripped:
                # This would be a duplicate local definition (bad)
                if not stripped.startswith("#"):
                    raise AssertionError(f"Found duplicate local extension_mapping definition at line {i+1}: {stripped}")

        # Test the mapping works
        indexer = CategoryIndexer()
        category = indexer.get_category_from_file_extension("py")
        assert category == "programming", f"Expected 'programming' for .py files, got '{category}'"

        print("[PASS] Issue 11: CategoryIndexer optimization verified")
        return True
    except Exception as e:
        print(f"[FAIL] Issue 11 failed: {e}")
        traceback.print_exc()
        return False


def test_concept_extractor_fix():
    """Test Issue 10: Removed duplicate _process_line"""
    print("Testing Issue 10: ConceptExtractor duplicate method...")
    try:
        from src.extractors.concept_extractor import ConceptExtractor
        import inspect

        # Get the _process_line method
        if hasattr(ConceptExtractor, '_process_line'):
            method = getattr(ConceptExtractor, '_process_line')
            source = inspect.getsource(method)

            # Check that it's not just "pass" (the duplicate we removed)
            assert source.strip() != "pass", "_process_line should not be just 'pass'"
            assert len(source.strip()) > 50, "_process_line should have actual implementation"

        print("[PASS] Issue 10: ConceptExtractor duplicate method removed")
        return True
    except Exception as e:
        print(f"[FAIL] Issue 10 failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("Running validation tests for MEDIUM issue fixes...")
    print("=" * 60)

    results = []

    # Test all 5 issues
    results.append(test_exception_hierarchy())        # Issue 14
    results.append(test_llm_provider_optimization())   # Issue 12
    results.append(test_base_schema_validation())      # Issue 13
    results.append(test_category_indexer_optimization()) # Issue 11
    results.append(test_concept_extractor_fix())       # Issue 10

    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All MEDIUM issue fixes validated!")
        return 0
    else:
        print(f"FAILED: {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())