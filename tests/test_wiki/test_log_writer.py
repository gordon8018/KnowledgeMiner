import pytest
import os
from datetime import datetime
from src.wiki.writers.log_writer import LogWriter
from src.wiki.models import WikiUpdate, UpdateType

def test_append_ingest_log():
    """Test appending ingest log entry"""
    log_entry = WikiUpdate(
        timestamp=datetime.now(),
        update_type=UpdateType.INGEST,
        page_id="test-paper",
        changes="Created new page from source",
        parent_version=0
    )

    writer = LogWriter()
    writer.append_ingest("raw/papers/test.md", ["test-paper"])

    # Check file exists
    assert os.path.exists("wiki/log.md")

    # Check content
    with open("wiki/log.md", "r", encoding="utf-8") as f:
        content = f.read()

    assert "## [2026" in content  # Date format
    assert "ingest" in content
    assert "test-paper" in content

    # Cleanup
    os.remove("wiki/log.md")
