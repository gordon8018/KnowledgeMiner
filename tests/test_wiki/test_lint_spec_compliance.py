"""
Comprehensive test to verify all 6 lint requirements are implemented
"""

import pytest
import os
from src.wiki.operations.lint import (
    lint_wiki,
    OrphanDetector,
    BrokenLinkDetector,
    FrontmatterDetector,
    EmptyPageDetector,
    LintReport
)


class TestAllSixRequirements:
    """Test that all 6 requirements from the spec are implemented"""

    def test_requirement_1_detect_orphan_pages(self):
        """Requirement 1: Detect orphan pages (pages with no inbound links)"""
        os.makedirs("wiki/concepts", exist_ok=True)

        # Create an orphan page (nothing links to it)
        with open("wiki/concepts/orphan.md", "w") as f:
            f.write("# Orphan\n\nThis page has no inbound links.")

        # Create a page that links to the orphan
        with open("wiki/concepts/linked.md", "w") as f:
            f.write("# Linked\n\nThis page links to [[orphan]].")

        detector = OrphanDetector()
        orphans = detector.find([
            "wiki/concepts/orphan.md",
            "wiki/concepts/linked.md"
        ])

        # "linked" is an orphan because nothing links to it
        assert "linked" in orphans
        # "orphan" is NOT an orphan because linked.md links to it
        assert "orphan" not in orphans

        # Cleanup
        os.remove("wiki/concepts/orphan.md")
        os.remove("wiki/concepts/linked.md")

    def test_requirement_2_detect_broken_links(self):
        """Requirement 2: Detect broken links (links to non-existent pages)"""
        os.makedirs("wiki/concepts", exist_ok=True)

        # Create a page with a broken link
        with open("wiki/concepts/broken.md", "w") as f:
            f.write("# Broken\n\nThis links to [[nonexistent]].")

        detector = BrokenLinkDetector()
        broken = detector.find(
            ["wiki/concepts/broken.md"],
            ["broken"]  # Only "broken" exists, not "nonexistent"
        )

        assert "broken" in broken
        assert "nonexistent" in broken["broken"]

        # Cleanup
        os.remove("wiki/concepts/broken.md")

    def test_requirement_3_detect_missing_frontmatter(self):
        """Requirement 3: Detect missing frontmatter"""
        os.makedirs("wiki/concepts", exist_ok=True)

        # Page with frontmatter
        with open("wiki/concepts/with_fm.md", "w") as f:
            f.write("---\ntitle: Test\n---\n\nContent")

        # Page without frontmatter
        with open("wiki/concepts/without_fm.md", "w") as f:
            f.write("# No Frontmatter\n\nContent")

        detector = FrontmatterDetector()
        missing = detector.find([
            "wiki/concepts/with_fm.md",
            "wiki/concepts/without_fm.md"
        ])

        assert "without_fm" in missing
        assert "with_fm" not in missing

        # Cleanup
        os.remove("wiki/concepts/with_fm.md")
        os.remove("wiki/concepts/without_fm.md")

    def test_requirement_4_detect_empty_pages(self):
        """Requirement 4: Detect empty or near-empty pages"""
        os.makedirs("wiki/concepts", exist_ok=True)

        # Empty page (with frontmatter but no content)
        with open("wiki/concepts/empty.md", "w") as f:
            f.write("---\ntitle: Empty\n---\n\n")

        # Page with substantial content
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

    def test_requirement_5_generate_lint_reports(self):
        """Requirement 5: Generate lint reports with all required fields"""
        os.makedirs("wiki/concepts", exist_ok=True)

        # Create test pages with various issues
        with open("wiki/concepts/page1.md", "w") as f:
            f.write("# Page 1\n\nContent.")

        with open("wiki/concepts/orphan.md", "w") as f:
            f.write("# Orphan\n\nNo links to this page.")

        report = lint_wiki()

        # Verify LintReport has all required fields
        assert hasattr(report, 'total_pages')
        assert hasattr(report, 'issues_found')
        assert hasattr(report, 'issues_fixed')
        assert hasattr(report, 'recommendations')

        # Verify field types
        assert isinstance(report.total_pages, int)
        assert isinstance(report.issues_found, int)
        assert isinstance(report.issues_fixed, int)
        assert isinstance(report.recommendations, list)

        # Verify we found at least the orphan
        assert report.total_pages >= 2
        assert report.issues_found >= 1

        # Cleanup
        os.remove("wiki/concepts/page1.md")
        os.remove("wiki/concepts/orphan.md")

    def test_requirement_6_support_auto_fix(self):
        """Requirement 6: Support auto-fix for some issues"""
        os.makedirs("wiki/concepts", exist_ok=True)

        # Create page missing frontmatter
        with open("wiki/concepts/fixme.md", "w") as f:
            f.write("# No Frontmatter\n\nSome content here")

        # Run lint with auto_fix=False
        report_no_fix = lint_wiki(auto_fix=False)
        initial_issues_fixed = report_no_fix.issues_fixed

        # Run lint with auto_fix=True
        report_with_fix = lint_wiki(auto_fix=True)

        # Should have fixed at least the frontmatter issue
        assert report_with_fix.issues_fixed >= initial_issues_fixed

        # Verify the frontmatter was actually added
        with open("wiki/concepts/fixme.md", "r") as f:
            content = f.read()
            assert content.startswith("---"), "Frontmatter should have been added"
            assert "title:" in content, "Title should be in frontmatter"

        # Cleanup
        os.remove("wiki/concepts/fixme.md")

    def test_all_detectors_are_callable(self):
        """Verify all detector classes have find() methods"""
        assert callable(OrphanDetector().find)
        assert callable(BrokenLinkDetector().find)
        assert callable(FrontmatterDetector().find)
        assert callable(EmptyPageDetector().find)

    def test_lint_wiki_accepts_auto_fix_parameter(self):
        """Verify lint_wiki() accepts auto_fix parameter"""
        # Should not raise an error
        report1 = lint_wiki(auto_fix=False)
        report2 = lint_wiki(auto_fix=True)

        assert isinstance(report1, LintReport)
        assert isinstance(report2, LintReport)
