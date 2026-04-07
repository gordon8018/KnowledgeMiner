import pytest
from src.wiki.operations.index_searcher import IndexSearcher

def test_search_index():
    """Test searching wiki index"""
    # Create a test index
    index_content = """
    # KnowledgeMiner Wiki Index

    ## Concepts
    - [[concept1|Machine Learning]] - A subset of AI
    - [[concept2|Deep Learning]] - A type of ML

    ## Entities
    - [[entity1|OpenAI]] - AI company
    """

    with open("wiki/index.md", "w") as f:
        f.write(index_content)

    searcher = IndexSearcher()
    results = searcher.search("machine learning")

    assert len(results) > 0
    assert "concept1" in results

    # Cleanup
    import os
    os.remove("wiki/index.md")
