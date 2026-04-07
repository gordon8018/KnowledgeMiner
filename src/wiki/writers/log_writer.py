"""
Log writing functionality for wiki
"""

import os
from datetime import datetime
from typing import List
from src.wiki.models import WikiUpdate, UpdateType


class LogWriter:
    """
    Writes wiki update log to disk
    """

    def append_ingest(self, source_path: str, page_ids: List[str]) -> None:
        """
        Append ingest operation to log

        Args:
            source_path: Path to ingested source
            page_ids: List of page IDs that were created/updated
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M")

        entry = f"""## [{date_str} {time_str}] ingest | {os.path.basename(source_path)}

**Source:** {source_path}
**Pages created/updated:** {len(page_ids)}
**Page IDs:** {", ".join(page_ids)}

"""

        self._append_to_log(entry)

    def append_query(self, question: str, page_id: str = None) -> None:
        """
        Append query operation to log

        Args:
            question: Query string
            page_id: Page ID if new page was created (optional)
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M")

        if page_id:
            entry = f"""## [{date_str} {time_str}] query | {question[:50]}...

**Question:** {question}
**New page created:** {page_id}

"""
        else:
            entry = f"""## [{date_str} {time_str}] query | {question[:50]}...

**Question:** {question}

"""

        self._append_to_log(entry)

    def append_lint(self, report) -> None:
        """
        Append lint operation to log

        Args:
            report: LintReport instance
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M")

        entry = f"""## [{date_str} {time_str}] lint | Health check

**Pages checked:** {report.total_pages}
**Issues found:** {report.issues_found}
**Issues fixed:** {report.issues_fixed}

"""

        self._append_to_log(entry)

    def _append_to_log(self, entry: str) -> None:
        """
        Append entry to log file

        Args:
            entry: Log entry content
        """
        log_path = "wiki/log.md"

        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Append to log
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
