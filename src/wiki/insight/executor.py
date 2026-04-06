"""
BackfillExecutor for executing Wiki page backfill operations.

This module provides the BackfillExecutor class that integrates insights
into Wiki pages by updating content and creating version records.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.wiki.core.models import WikiPage, WikiVersion, PageType
from src.wiki.core.storage import WikiStore
from src.discovery.models.insight import Insight


logger = logging.getLogger(__name__)


class BackfillExecutor:
    """
    Execute backfill operations to integrate insights into Wiki pages.

    The BackfillExecutor:
    1. Finds Wiki pages affected by an insight
    2. Updates page content using LLM-generated intelligent updates
    3. Creates version records for all changes
    4. Orchestrates the complete backfill workflow
    """

    def __init__(self, wiki_store: WikiStore, llm_provider: Any):
        """
        Initialize BackfillExecutor.

        Args:
            wiki_store: WikiStore instance for page operations
            llm_provider: LLM provider for content generation
        """
        self.wiki_store = wiki_store
        self.llm_provider = llm_provider
        self._author = "backfill_executor"

    def find_target_pages(self, insight: Insight) -> List[WikiPage]:
        """
        Find Wiki pages affected by the insight.

        Searches for pages that reference the insight's related concepts.
        Uses concept names directly as page IDs.

        Args:
            insight: Insight to find target pages for

        Returns:
            List of WikiPage objects affected by the insight
        """
        target_pages = []
        seen_page_ids = set()

        # Search for pages matching each related concept
        for concept in insight.related_concepts:
            # Use concept name directly as page ID
            page_id = concept

            try:
                page = self.wiki_store.get_page(page_id)

                if page and page.id not in seen_page_ids:
                    target_pages.append(page)
                    seen_page_ids.add(page.id)
                    logger.debug(f"Found target page {page.id} for concept {concept}")

            except Exception as e:
                logger.warning(f"Error searching for page {page_id}: {e}")
                continue

        logger.info(f"Found {len(target_pages)} target pages for insight {insight.id}")
        return target_pages

    def update_page_content(self, page: WikiPage, insight: Insight) -> WikiPage:
        """
        Update page content with new insight using LLM.

        Generates an intelligent update that:
        - Preserves existing page structure and content
        - Adds insight to appropriate section (e.g., "## Insights")
        - Maintains markdown formatting

        Args:
            page: WikiPage to update
            insight: Insight to integrate into page

        Returns:
            Updated WikiPage with incremented version

        Raises:
            Exception: If LLM generation fails
        """
        # Generate update prompt for LLM
        prompt = self._create_update_prompt(page, insight)

        try:
            # Use LLM to generate updated content
            updated_content = self.llm_provider.generate(prompt)

            # Create updated page object
            updated_page = WikiPage(
                id=page.id,
                title=page.title,
                content=updated_content,
                page_type=page.page_type,
                version=page.version,
                metadata=page.metadata.copy(),
                created_at=page.created_at,
                updated_at=datetime.now()
            )

            # Increment version
            updated_page.increment_version()

            logger.info(f"Generated content update for page {page.id} using insight {insight.id}")
            return updated_page

        except Exception as e:
            logger.error(f"Failed to generate content update for page {page.id}: {e}")
            raise

    def _create_update_prompt(self, page: WikiPage, insight: Insight) -> str:
        """
        Create prompt for LLM to update page content with insight.

        Args:
            page: WikiPage to update
            insight: Insight to integrate

        Returns:
            Prompt string for LLM
        """
        prompt = f"""You are updating a Wiki page to incorporate a new insight.

**Current Page Content:**
```
{page.content}
```

**New Insight to Add:**
- Title: {insight.title}
- Description: {insight.description}
- Type: {insight.insight_type.value}
- Significance: {insight.significance:.2f}

**Instructions:**
1. Preserve all existing content and structure
2. Add the insight to an "## Insights" section (create it if it doesn't exist)
3. Format the insight as a bullet point with the title in bold
4. Include the description after the title
5. Maintain proper markdown formatting
6. Do not remove or alter existing insights

**Updated Page Content:**
"""

        return prompt

    def create_new_version(
        self,
        page: WikiPage,
        change_summary: str,
        author: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WikiVersion:
        """
        Create version record for updated page.

        Args:
            page: Updated WikiPage
            change_summary: Description of changes made
            author: Author of the change (default: "backfill_executor")
            metadata: Additional metadata to attach to version

        Returns:
            WikiVersion object representing the new version
        """
        parent_version = page.version - 1

        version_metadata = {
            "updated_at": datetime.now().isoformat(),
            "insight_backfill": True
        }

        if metadata:
            version_metadata.update(metadata)

        version = WikiVersion(
            page_id=page.id,
            version=page.version,
            content=page.content,
            parent_version=parent_version,
            change_summary=change_summary,
            created_at=datetime.now(),
            author=author or self._author,
            metadata=version_metadata
        )

        logger.debug(
            f"Created version record for page {page.id}, "
            f"version {page.version}, parent {parent_version}"
        )

        return version

    def backfill_insight(self, insight: Insight) -> List[str]:
        """
        Main orchestration method to backfill an insight into Wiki pages.

        Workflow:
        1. Find target pages affected by the insight
        2. Update each page's content with the insight
        3. Create version records for all changes
        4. Persist updates to WikiStore

        Args:
            insight: Insight to backfill into Wiki

        Returns:
            List of updated page IDs

        Raises:
            Exception: If any page update fails
        """
        if not insight.related_concepts:
            logger.info(f"Insight {insight.id} has no related concepts, skipping backfill")
            return []

        # Find target pages
        target_pages = self.find_target_pages(insight)

        if not target_pages:
            logger.info(f"No target pages found for insight {insight.id}")
            return []

        updated_page_ids = []

        # Update each target page
        for page in target_pages:
            try:
                # Generate updated content
                updated_page = self.update_page_content(page, insight)

                # Create version record
                change_summary = f"Added insight: {insight.title}"
                version = self.create_new_version(
                    updated_page,
                    change_summary,
                    metadata={"insight_id": insight.id}
                )

                # Persist update to WikiStore
                self.wiki_store.update_page(updated_page)

                updated_page_ids.append(updated_page.id)
                logger.info(f"Successfully backfilled insight {insight.id} to page {updated_page.id}")

            except Exception as e:
                logger.error(f"Failed to backfill insight {insight.id} to page {page.id}: {e}")
                raise

        logger.info(
            f"Completed backfill for insight {insight.id}, "
            f"updated {len(updated_page_ids)} pages"
        )

        return updated_page_ids

    def set_author(self, author: str) -> None:
        """
        Set the author name for version records.

        Args:
            author: Author name to use
        """
        self._author = author
        logger.debug(f"Set backfill executor author to: {author}")
