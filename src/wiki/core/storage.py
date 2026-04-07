"""WikiStore storage engine with Git + SQLite."""

import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import shutil
import json

from src.wiki.core.models import WikiPage, WikiVersion, PageType


class WikiStore:
    """
    Simplified Wiki storage engine.

    Stores Wiki pages as markdown files with Git version control.
    Uses SQLite for metadata and indexing.
    """

    def __init__(self, storage_path: str):
        """
        Initialize WikiStore.

        Args:
            storage_path: Path to wiki storage directory
        """
        self.storage_path = Path(storage_path)
        self.topics_dir = self.storage_path / "topics"
        self.concepts_dir = self.storage_path / "concepts"
        self.relations_dir = self.storage_path / "relations"
        self.meta_dir = self.storage_path / "meta"
        self.schema_dir = self.storage_path / "schema"

        # Create directories
        for dir_path in [self.topics_dir, self.concepts_dir,
                        self.relations_dir, self.meta_dir,
                        self.schema_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database
        self.db_path = self.meta_dir / "wiki.db"
        self._init_database()

        # Initialize Git repository
        self._init_git()

    def _init_database(self):
        """Initialize SQLite database for metadata."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                page_type TEXT NOT NULL,
                version INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                metadata TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                parent_version INTEGER,
                change_summary TEXT,
                created_at TIMESTAMP,
                author TEXT,
                FOREIGN KEY (page_id) REFERENCES pages(id)
            )
        """)
        self.conn.commit()

    def _init_git(self):
        """Initialize Git repository for version control."""
        import subprocess

        # Initialize .git if not exists
        git_dir = self.storage_path / ".git"
        if not git_dir.exists():
            result = subprocess.run(
                ["git", "init"],
                cwd=str(self.storage_path),
                capture_output=True
            )
            # BUGFIX: LOW #2 - Check git init return code
            if result.returncode != 0:
                raise RuntimeError(f"Failed to initialize git repository: {result.stderr.decode()}")

    def _get_page_dir(self, page_type: PageType) -> Path:
        """Get directory for a page type."""
        if page_type == PageType.TOPIC:
            return self.topics_dir
        elif page_type == PageType.CONCEPT:
            return self.concepts_dir
        else:  # RELATION
            return self.relations_dir

    def _get_page_path(self, page_id: str, page_type: PageType) -> Path:
        """Get file path for a page."""
        dir_path = self._get_page_dir(page_type)
        return dir_path / f"{page_id}.md"

    def create_page(self, page: WikiPage) -> WikiPage:
        """
        Create a new Wiki page.

        Args:
            page: WikiPage to create

        Returns:
            Created WikiPage with updated metadata
        """
        # Check if page already exists
        if self.get_page(page.id):
            raise ValueError(f"Page {page.id} already exists")

        # Save page content to file
        file_path = self._get_page_path(page.id, page.page_type)
        file_path.write_text(page.content)

        # Git commit FIRST (easier to rollback if it fails) (BUGFIX: NEW #3)
        try:
            self._git_commit(f"Create page: {page.id}", [str(file_path.relative_to(self.storage_path))])
        except RuntimeError as e:
            # Git failed - cleanup file and re-raise
            if file_path.exists():
                file_path.unlink()
            raise e

        # Git succeeded - now update database
        self.conn.execute(
            "INSERT INTO pages (id, title, page_type, version, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (page.id, page.title, page.page_type.value, page.version,
             page.created_at.isoformat(), page.updated_at.isoformat(), json.dumps(page.metadata))
        )
        self.conn.commit()

        return page

    def get_page(self, page_id: str) -> Optional[WikiPage]:
        """
        Retrieve a Wiki page by ID.

        Args:
            page_id: Page ID to retrieve

        Returns:
            WikiPage if found, None otherwise
        """
        # Query database
        cursor = self.conn.execute(
            "SELECT * FROM pages WHERE id = ?",
            (page_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        # Read content from file
        cursor = self.conn.execute("SELECT page_type FROM pages WHERE id = ?", (page_id,))
        page_type_str = cursor.fetchone()[0]
        page_type = PageType(page_type_str)

        file_path = self._get_page_path(page_id, page_type)
        content = file_path.read_text() if file_path.exists() else ""

        return WikiPage(
            id=row[0],
            title=row[1],
            content=content,
            page_type=PageType(row[2]),
            version=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            metadata=json.loads(row[6]) if row[6] else {}
        )

    def update_page(self, page: WikiPage) -> WikiPage:
        """
        Update an existing Wiki page.

        Args:
            page: WikiPage with updates

        Returns:
            Updated WikiPage with incremented version
        """
        # Check if page exists
        existing = self.get_page(page.id)
        if not existing:
            raise ValueError(f"Page {page.id} does not exist")

        # Save old state for rollback (BUGFIX: MEDIUM - save both version and updated_at)
        old_version = page.version
        old_updated_at = page.updated_at

        # Increment version
        new_version = page.increment_version()

        # Update file
        file_path = self._get_page_path(page.id, page.page_type)
        file_path.write_text(page.content)

        # Git commit FIRST (easier to rollback if it fails) (BUGFIX: NEW #3)
        try:
            self._git_commit(f"Update page: {page.id}", [str(file_path.relative_to(self.storage_path))])
        except RuntimeError as e:
            # Git failed - rollback file and page state
            file_path.write_text(existing.content)  # Restore original content
            page.version = old_version  # Restore version
            page.updated_at = old_updated_at  # BUGFIX: Restore updated_at
            raise e

        # Git succeeded - now update database
        self.conn.execute(
            "UPDATE pages SET title = ?, version = ?, updated_at = ?, metadata = ? WHERE id = ?",
            (page.title, new_version, page.updated_at.isoformat(), json.dumps(page.metadata), page.id)
        )

        # Record version
        self.conn.execute(
            "INSERT INTO versions (page_id, version, parent_version, change_summary, created_at) VALUES (?, ?, ?, ?, ?)",
            (page.id, new_version, old_version, "Page updated", page.updated_at.isoformat())
        )
        self.conn.commit()

        return page

    def delete_page(self, page_id: str) -> bool:
        """
        Delete a Wiki page.

        Args:
            page_id: Page ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Get page info before deleting
        page = self.get_page(page_id)
        if not page:
            return False

        # Get file path
        file_path = self._get_page_path(page_id, page.page_type)
        relative_path = str(file_path.relative_to(self.storage_path))

        # Delete file FIRST (BUGFIX: CRITICAL - so git add stages the deletion)
        # When file exists: git add stages content
        # When file doesn't exist: git add stages deletion
        if file_path.exists():
            file_path.unlink()

        # Git commit (git add will stage the deletion since file doesn't exist)
        try:
            self._git_commit(f"Delete page: {page_id}", [relative_path])
        except RuntimeError as e:
            # Git failed - we already deleted the file
            # Log the error but continue with DB deletion (DB is the source of truth)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Git commit failed for page deletion: {e}")
            # Continue with DB deletion since file is already deleted

        # Delete from database
        self.conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))
        self.conn.execute("DELETE FROM versions WHERE page_id = ?", (page_id,))
        self.conn.commit()

        return True

    def _git_commit(self, message: str, files: List[str]):
        """Create a Git commit."""
        import subprocess

        # Add files
        for file_path in files:
            result = subprocess.run(
                ["git", "add", file_path],
                cwd=str(self.storage_path),
                capture_output=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to git add {file_path}: {result.stderr.decode()}")

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(self.storage_path),
            capture_output=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to git commit: {result.stderr.decode()}")

    def __del__(self):
        """Cleanup database connection when object is destroyed."""
        if hasattr(self, 'conn') and self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass  # Ignore errors during cleanup

    def close(self):
        """Explicitly close the database connection."""
        if hasattr(self, 'conn') and self.conn is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Support for context manager protocol (BUGFIX: MED-1)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit (BUGFIX: MED-1)."""
        self.close()
        return False  # Don't suppress exceptions
