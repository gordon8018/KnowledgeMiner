import pytest
import tempfile
import os
import json
from src.main import KnowledgeCompiler


def test_compile_documents():
    """Integration test as specified in Task 12."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = os.path.join(temp_dir, "source")
        target_dir = os.path.join(temp_dir, "target")
        os.makedirs(source_dir)

        test_doc = os.path.join(source_dir, "test.md")
        with open(test_doc, 'w', encoding='utf-8') as f:
            f.write("# 测试\n\n「弱转强」是重要形态。")

        config = {
            "source_dir": source_dir,
            "target_dir": target_dir,
            "categories": ["技术指标", "战法"],
            "extraction": {"min_confidence": 0.5}
        }

        compiler = KnowledgeCompiler(config)
        compiler.compile()

        # Verify outputs exist
        assert os.path.exists(os.path.join(target_dir, "summaries", "test.md"))
        assert os.path.exists(os.path.join(target_dir, "INDEX.md"))
        assert os.path.exists(os.path.join(target_dir, ".hashes.json"))
