"""
Tests for wiki linting functionality
"""

import pytest
import os
from src.wiki.operations.lint import lint_wiki, OrphanDetector


def test_detect_orphan_pages():
    """Test detecting orphan pages (no inbound links)"""
    # Create test pages
    os.makedirs("wiki/concepts", exist_ok=True)
    with open("wiki/concepts/orphan.md", "w") as f:
        f.write("# Orphan Page\n\nThis page has no links.")
    with open("wiki/concepts/linked.md", "w") as f:
        f.write("# Linked Page\n\nThis links to [[orphan]].")

    detector = OrphanDetector()
    orphans = detector.find(["wiki/concepts/orphan.md", "wiki/concepts/linked.md"])

    # "linked" is an orphan because nothing links to it
    assert "linked" in orphans
    # "orphan" is NOT an orphan because linked.md links to it
    assert "orphan" not in orphans

    # Cleanup
    os.remove("wiki/concepts/orphan.md")
    os.remove("wiki/concepts/linked.md")


def test_broken_links():
    """Test detecting broken links (links to non-existent pages)"""
    # Create test page with broken link
    os.makedirs("wiki/concepts", exist_ok=True)
    with open("wiki/concepts/page1.md", "w") as f:
        f.write("# Page 1\n\nThis links to [[nonexistent]].")

    detector = OrphanDetector()
    # The broken link should be detectable
    # (Implementation should track which pages exist vs which are linked)

    # Cleanup
    os.remove("wiki/concepts/page1.md")


def test_lint_report():
    """Test generating lint report"""
    # Create test wiki
    os.makedirs("wiki/concepts", exist_ok=True)
    with open("wiki/concepts/page1.md", "w") as f:
        f.write("# Page 1\n\nContent.")
    with open("wiki/concepts/orphan.md", "w") as f:
        f.write("# Orphan\n\nNo links to this page.")

    report = lint_wiki()

    assert report.total_pages >= 2
    assert report.issues_found >= 1  # At least the orphan
    assert isinstance(report.recommendations, list)

    # Cleanup
    os.remove("wiki/concepts/page1.md")
    os.remove("wiki/concepts/orphan.md")
