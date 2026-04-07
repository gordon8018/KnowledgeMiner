"""
Wiki linting functionality for health checks
"""

import os
import shutil
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.wiki.constants import WIKILINK_PATTERN, WIKI_DIRECTORIES, MARKDOWN_EXTENSION


@dataclass
class LintReport:
    """Report from linting wiki"""
    total_pages: int
    issues_found: int
    issues_fixed: int
    recommendations: List[str]


def _read_pages(page_paths: List[str]) -> Dict[str, str]:
    """
    Read and parse page contents from file paths.

    Helper function to eliminate code duplication across detector classes.
    Reads all markdown files and returns a dictionary mapping page IDs to content.

    Args:
        page_paths: List of page file paths to read

    Returns:
        Dictionary mapping {page_id: content} for successfully read pages
    """
    pages = {}
    for page_path in page_paths:
        if not os.path.exists(page_path):
            continue

        page_id = os.path.basename(page_path).replace(MARKDOWN_EXTENSION, "")

        try:
            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()
            pages[page_id] = content
        except (IOError, OSError) as e:
            # Skip files that can't be read (permissions, encoding issues)
            continue

    return pages


class OrphanDetector:
    """
    Detects orphan pages (pages with no inbound links)
    """

    def find(self, page_paths: List[str]) -> List[str]:
        """
        Find orphan pages

        Args:
            page_paths: List of page file paths

        Returns:
            List of orphan page IDs (without .md extension)
        """
        # Read all pages using shared helper
        pages = _read_pages(page_paths)

        # Collect all links from all pages (excluding self-links)
        all_links = set()
        page_to_links = {}  # Track which links each page contains

        for page_id, content in pages.items():
            # Find all wikilinks using shared pattern
            matches = WIKILINK_PATTERN.findall(content)

            # Filter out self-links and clean up display text
            outbound_links = []
            for link in matches:
                # Handle [[page|display]] format
                link_id = link.split("|")[0].strip()
                if link_id and link_id != page_id:
                    outbound_links.append(link_id)

            page_to_links[page_id] = outbound_links
            all_links.update(outbound_links)

        # Find orphans (pages not linked to by any other page)
        orphans = [page_id for page_id in pages.keys() if page_id not in all_links]

        return orphans


class BrokenLinkDetector:
    """
    Detects broken links (links to non-existent pages)
    """

    def find(self, page_paths: List[str], existing_pages: List[str]) -> Dict[str, List[str]]:
        """
        Find broken links

        Args:
            page_paths: List of page file paths to check
            existing_pages: List of existing page IDs

        Returns:
            Dict mapping {page_id: [broken_links]}
        """
        # Read all pages using shared helper
        pages = _read_pages(page_paths)

        broken_links = {}
        existing_set = set(existing_pages)

        for page_id, content in pages.items():
            # Find all wikilinks using shared pattern
            matches = WIKILINK_PATTERN.findall(content)

            # Check if each link exists (handle [[page|display]] format)
            page_broken_links = []
            for link in matches:
                link_id = link.split("|")[0].strip()
                if link_id and link_id not in existing_set:
                    page_broken_links.append(link_id)

            if page_broken_links:
                broken_links[page_id] = page_broken_links

        return broken_links


class FrontmatterDetector:
    """
    Detects pages missing frontmatter
    """

    def find(self, page_paths: List[str]) -> List[str]:
        """
        Find pages missing frontmatter

        Args:
            page_paths: List of page file paths

        Returns:
            List of page IDs missing frontmatter
        """
        # Read all pages using shared helper
        pages = _read_pages(page_paths)

        # Check for pages missing frontmatter
        pages_missing = [
            page_id for page_id, content in pages.items()
            if not content.strip().startswith("---")
        ]

        return pages_missing


class EmptyPageDetector:
    """
    Detects empty or near-empty pages
    """

    def find(self, page_paths: List[str], min_content_length: int = 50) -> List[str]:
        """
        Find empty or near-empty pages

        Args:
            page_paths: List of page file paths
            min_content_length: Minimum content length (characters)

        Returns:
            List of page IDs with insufficient content
        """
        # Read all pages using shared helper
        pages = _read_pages(page_paths)

        empty_pages = []
        for page_id, content in pages.items():
            # Remove YAML frontmatter from content check
            check_content = content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    check_content = parts[2].strip()

            # Check content length
            if len(check_content) < min_content_length:
                empty_pages.append(page_id)

        return empty_pages


def lint_wiki(auto_fix: bool = False) -> LintReport:
    """
    Lint the wiki and generate a report

    Args:
        auto_fix: If True, attempt to auto-fix issues (with backup/rollback safety)

    Returns:
        LintReport with findings
    """
    from src.wiki.operations.page_reader import PageReader

    reader = PageReader()
    all_pages = reader.list_all()

    issues = []
    fixes = []
    recommendations = []
    backup_path = None

    # Build page paths for all directories using constant
    page_paths = []
    for page_id in all_pages:
        # Try each directory from WIKI_DIRECTORIES
        for directory in WIKI_DIRECTORIES:
            path = f"wiki/{directory}/{page_id}{MARKDOWN_EXTENSION}"
            if os.path.exists(path):
                page_paths.append(path)
                break

    # Create backup before auto-fix
    if auto_fix:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"wiki/.backup/backup_{timestamp}"
        try:
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            # Create backup by copying wiki directory
            if os.path.exists("wiki"):
                shutil.copytree("wiki", backup_path)
                fixes.append(f"Created backup at {backup_path}")
        except (OSError, shutil.Error) as e:
            # If backup fails, disable auto-fix for safety
            issues.append(f"Backup failed, auto-fix disabled: {e}")
            auto_fix = False

    try:
        # Check for orphans
        orphan_detector = OrphanDetector()
        orphans = orphan_detector.find(page_paths)
        for orphan in orphans:
            issues.append(f"Orphan page: {orphan}")
            recommendations.append(f"Consider adding links to [[{orphan}]] from related pages")

        # Check for broken links
        broken_detector = BrokenLinkDetector()
        broken_links = broken_detector.find(page_paths, all_pages)
        for page_id, links in broken_links.items():
            for link in links:
                issues.append(f"Broken link in {page_id}: [[{link}]]")
                recommendations.append(f"Create page for {link} or remove link")

        # Check for missing frontmatter
        frontmatter_detector = FrontmatterDetector()
        missing_frontmatter = frontmatter_detector.find(page_paths)
        for page_id in missing_frontmatter:
            issues.append(f"Missing frontmatter: {page_id}")
            recommendations.append(f"Add YAML frontmatter to {page_id}")

            # Auto-fix: Add basic frontmatter (with error handling)
            if auto_fix:
                page_path = None
                for directory in WIKI_DIRECTORIES:
                    path = f"wiki/{directory}/{page_id}{MARKDOWN_EXTENSION}"
                    if os.path.exists(path):
                        page_path = path
                        break

                if page_path:
                    try:
                        with open(page_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Add basic frontmatter
                        frontmatter = f"---\ntitle: {page_id.replace('_', ' ').title()}\ncreated: {datetime.now().strftime('%Y-%m-%d')}\n---\n\n{content}"
                        with open(page_path, "w", encoding="utf-8") as f:
                            f.write(frontmatter)

                        fixes.append(f"Added frontmatter to {page_id}")
                    except (IOError, OSError) as e:
                        issues.append(f"Failed to add frontmatter to {page_id}: {e}")

        # Check for empty pages
        empty_detector = EmptyPageDetector()
        empty_pages = empty_detector.find(page_paths)
        for page_id in empty_pages:
            issues.append(f"Empty or near-empty page: {page_id}")
            recommendations.append(f"Add content to {page_id}")

    except Exception as e:
        # On error, rollback from backup if auto-fix was enabled
        if auto_fix and backup_path and os.path.exists(backup_path):
            try:
                # Remove current wiki and restore from backup
                shutil.rmtree("wiki")
                shutil.copytree(backup_path, "wiki")
                issues.append(f"Auto-fix failed, rolled back to backup: {e}")
                # Don't count partial fixes as successful
                fixes = [f"Created backup at {backup_path}"]
            except (OSError, shutil.Error) as rollback_error:
                issues.append(f"Critical: Auto-fix failed and rollback failed: {e} | {rollback_error}")
        else:
            issues.append(f"Error during lint: {e}")

    return LintReport(
        total_pages=len(all_pages),
        issues_found=len(issues),
        issues_fixed=len(fixes),
        recommendations=recommendations
    )
