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
            subprocess.run(
                ["git", "init"],
                cwd=str(self.storage_path),
                capture_output=True
            )

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

        # Insert metadata into database
        self.conn.execute(
            "INSERT INTO pages (id, title, page_type, version, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (page.id, page.title, page.page_type.value, page.version,
             page.created_at.isoformat(), page.updated_at.isoformat(), json.dumps(page.metadata))
        )
        self.conn.commit()

        # Git commit
        self._git_commit(f"Create page: {page.id}", [str(file_path.relative_to(self.storage_path))])

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

        # Increment version
        old_version = page.version
        new_version = page.increment_version()

        # Update file
        file_path = self._get_page_path(page.id, page.page_type)
        file_path.write_text(page.content)

        # Update database
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

        # Git commit
        self._git_commit(f"Update page: {page.id}", [str(file_path.relative_to(self.storage_path))])

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

        # Delete file
        file_path = self._get_page_path(page_id, page.page_type)
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        self.conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))
        self.conn.execute("DELETE FROM versions WHERE page_id = ?", (page_id,))
        self.conn.commit()

        # Git commit
        self._git_commit(f"Delete page: {page_id}", [])

        return True

    def _git_commit(self, message: str, files: List[str]):
        """Create a Git commit."""
        import subprocess

        # Add files
        for file_path in files:
            subprocess.run(
                ["git", "add", file_path],
                cwd=str(self.storage_path),
                capture_output=True
            )

        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(self.storage_path),
            capture_output=True
        )
