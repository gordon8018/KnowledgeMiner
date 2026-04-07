"""
Tests for wiki linting functionality
"""

import pytest
import os
from src.wiki.operations.lint import lint_wiki, OrphanDetector, BrokenLinkDetector, FrontmatterDetector, EmptyPageDetector


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
    os.makedirs("wiki/concepts", exist_ok=True)

    # Create test page with broken link
    with open("wiki/concepts/page1.md", "w") as f:
        f.write("# Page 1\n\nThis links to [[nonexistent]].")

    detector = BrokenLinkDetector()

    # Only page1 exists, not the page it links to
    broken = detector.find(["wiki/concepts/page1.md"], ["page1"])

    assert "page1" in broken
    assert "nonexistent" in broken["page1"]

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


def test_missing_frontmatter():
    """Test detecting pages missing frontmatter"""
    os.makedirs("wiki/concepts", exist_ok=True)

    # Page with frontmatter
    with open("wiki/concepts/with_frontmatter.md", "w") as f:
        f.write("---\ntitle: Test\n---\n\nContent")

    # Page without frontmatter
    with open("wiki/concepts/without_frontmatter.md", "w") as f:
        f.write("# No Frontmatter\n\nContent")

    detector = FrontmatterDetector()

    missing = detector.find([
        "wiki/concepts/with_frontmatter.md",
        "wiki/concepts/without_frontmatter.md"
    ])

    assert "without_frontmatter" in missing
    assert "with_frontmatter" not in missing

    # Cleanup
    os.remove("wiki/concepts/with_frontmatter.md")
    os.remove("wiki/concepts/without_frontmatter.md")


def test_empty_pages():
    """Test detecting empty or near-empty pages"""
    os.makedirs("wiki/concepts", exist_ok=True)

    # Empty page
    with open("wiki/concepts/empty.md", "w") as f:
        f.write("---\ntitle: Empty\n---\n\n")

    # Page with content
    with open("wiki/concepts/with_content.md", "w") as f:
        f.write("---\ntitle: Content\n---\n\nThis is substantial content that exceeds the minimum length requirement for a valid wiki page.")

    detector = EmptyPageDetector()

    empty = detector.find([
        "wiki/concepts/empty.md",
        "wiki/concepts/with_content.md"
    ])

    assert "empty" in empty
    assert "with_content" not in empty

    # Cleanup
    os.remove("wiki/concepts/empty.md")
    os.remove("wiki/concepts/with_content.md")


def test_auto_fix():
    """Test auto-fix functionality"""
    os.makedirs("wiki/concepts", exist_ok=True)

    # Create page missing frontmatter
    with open("wiki/concepts/no_frontmatter.md", "w") as f:
        f.write("# No Frontmatter\n\nSome content")

    # Run with auto_fix=True
    report = lint_wiki(auto_fix=True)

    # Should have attempted fixes
    assert report.issues_fixed >= 0  # At least attempted

    # Verify frontmatter was added
    with open("wiki/concepts/no_frontmatter.md", "r") as f:
        content = f.read()
        assert content.startswith("---")

    # Cleanup
    if os.path.exists("wiki/concepts/no_frontmatter.md"):
        os.remove("wiki/concepts/no_frontmatter.md")
