"""
Wiki linting functionality for health checks
"""

import os
import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class LintReport:
    """Report from linting wiki"""
    total_pages: int
    issues_found: int
    issues_fixed: int
    recommendations: List[str]


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
        # Collect all links from all pages (excluding self-links)
        all_links = set()
        page_to_links = {}  # Track which links each page contains

        for page_path in page_paths:
            if not os.path.exists(page_path):
                continue

            page_id = os.path.basename(page_path).replace(".md", "")

            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all wikilinks
            pattern = r'\[\[([^\]|]+)'
            matches = re.findall(pattern, content)

            # Filter out self-links
            outbound_links = [m for m in matches if m != page_id]
            page_to_links[page_id] = outbound_links
            all_links.update(outbound_links)

        # Find orphans (pages not linked to by any other page)
        orphans = []
        for page_path in page_paths:
            page_id = os.path.basename(page_path).replace(".md", "")

            # A page is an orphan if no other page links to it
            if page_id not in all_links:
                orphans.append(page_id)

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
        broken_links = {}

        for page_path in page_paths:
            if not os.path.exists(page_path):
                continue

            page_id = os.path.basename(page_path).replace(".md", "")

            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all wikilinks
            pattern = r'\[\[([^\]|]+)'
            matches = re.findall(pattern, content)

            # Check if each link exists
            page_broken_links = []
            for link in matches:
                if link not in existing_pages:
                    page_broken_links.append(link)

            if page_broken_links:
                broken_links[page_id] = page_broken_links

        return broken_links


def lint_wiki() -> LintReport:
    """
    Lint the wiki and generate a report

    Returns:
        LintReport with findings
    """
    from src.wiki.operations.page_reader import PageReader

    reader = PageReader()
    all_pages = reader.list_all()

    issues = []
    fixes = []
    recommendations = []

    # Check for orphans
    detector = OrphanDetector()

    # Build page paths for all directories
    page_paths = []
    for page_id in all_pages:
        # Try each directory
        for directory in ["entities", "concepts", "sources", "synthesis", "comparisons"]:
            path = f"wiki/{directory}/{page_id}.md"
            if os.path.exists(path):
                page_paths.append(path)
                break

    orphans = detector.find(page_paths)

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

    return LintReport(
        total_pages=len(all_pages),
        issues_found=len(issues),
        issues_fixed=len(fixes),
        recommendations=recommendations
    )
