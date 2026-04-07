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
