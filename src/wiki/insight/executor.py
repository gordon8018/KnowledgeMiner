"""
BackfillExecutor for executing Wiki page backfill operations.

This module provides the BackfillExecutor class that integrates insights
into Wiki pages by updating content and creating version records.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps

from src.wiki.core.models import WikiPage, WikiVersion, PageType
from src.wiki.core.storage import WikiStore
from src.discovery.models.insight import Insight


logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)  # Exponential backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            # If we get here, all attempts failed
            raise last_exception

        return wrapper
    return decorator


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
            Exception: If LLM generation fails after all retry attempts
        """
        # Generate update prompt for LLM
        prompt = self._create_update_prompt(page, insight)

        # Use LLM to generate updated content with retry logic
        updated_content = self._generate_content_with_retry(prompt)

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

    @retry_with_exponential_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
    def _generate_content_with_retry(self, prompt: str) -> str:
        """
        Generate content using LLM with retry logic.

        Args:
            prompt: Prompt for LLM

        Returns:
            Generated content

        Raises:
            Exception: If LLM generation fails after all retry attempts
        """
        return self.llm_provider.generate(prompt)

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

        Transaction support: All page updates are collected first, then
        applied atomically. If any update fails, all changes are rolled back.

        Args:
            insight: Insight to backfill into Wiki

        Returns:
            List of updated page IDs

        Raises:
            Exception: If any page update fails (with rollback)
        """
        if not insight.related_concepts:
            logger.info(f"Insight {insight.id} has no related concepts, skipping backfill")
            return []

        # Find target pages
        target_pages = self.find_target_pages(insight)

        if not target_pages:
            logger.info(f"No target pages found for insight {insight.id}")
            return []

        # Phase 1: Collect all updates (prepare phase)
        updates = []
        original_pages = {}  # Store original pages for rollback

        try:
            for page in target_pages:
                # Store original page for potential rollback
                original_pages[page.id] = page

                # Generate updated content
                updated_page = self.update_page_content(page, insight)

                # Create version record
                change_summary = f"Added insight: {insight.title}"
                version = self.create_new_version(
                    updated_page,
                    change_summary,
                    metadata={"insight_id": insight.id}
                )

                # Collect update
                updates.append({
                    "page": updated_page,
                    "original_page": page,
                    "version": version
                })

                logger.debug(f"Prepared update for page {page.id} (insight {insight.id})")

            # Phase 2: Apply all updates atomically (commit phase)
            updated_page_ids = []

            for update in updates:
                try:
                    # Persist update to WikiStore
                    self.wiki_store.update_page(update["page"])
                    updated_page_ids.append(update["page"].id)
                    logger.info(
                        f"Successfully backfilled insight {insight.id} to page {update['page'].id}"
                    )

                except Exception as e:
                    # Transaction failed: attempt rollback
                    logger.error(
                        f"Failed to persist update for page {update['page'].id}: {e}. "
                        f"Attempting rollback..."
                    )
                    self._rollback_updates(updates, updated_page_ids)
                    raise

            logger.info(
                f"Completed backfill for insight {insight.id}, "
                f"updated {len(updated_page_ids)} pages"
            )

            return updated_page_ids

        except Exception as e:
            # Error in prepare phase: no partial updates applied
            logger.error(
                f"Failed to prepare backfill for insight {insight.id}: {e}. "
                f"No updates were applied."
            )
            raise

    def _rollback_updates(self, updates: List[Dict[str, Any]], committed_page_ids: List[str]) -> None:
        """
        Rollback updates for pages that were already committed.

        Args:
            updates: List of prepared updates
            committed_page_ids: List of page IDs that were successfully committed
        """
        logger.warning(f"Rolling back {len(committed_page_ids)} committed updates...")

        for update in updates:
            if update["page"].id in committed_page_ids:
                try:
                    # Restore original page
                    self.wiki_store.update_page(update["original_page"])
                    logger.debug(f"Rolled back page {update['page'].id}")
                except Exception as rollback_error:
                    logger.error(
                        f"Failed to rollback page {update['page'].id}: {rollback_error}. "
                        f"Manual intervention may be required."
                    )

        logger.warning("Rollback completed")

    def set_author(self, author: str) -> None:
        """
        Set the author name for version records.

        Args:
            author: Author name to use
        """
        self._author = author
        logger.debug(f"Set backfill executor author to: {author}")
