"""
Structured logging for knowledge compiler.

Provides consistent logging format with structured output for
log aggregation systems and monitoring tools.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextlib import contextmanager
from pathlib import Path


class StructuredLogger:
    """
    Structured logger with JSON formatting and context management.

    Features:
    - Consistent JSON log format
    - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - Context-aware logging with automatic correlation IDs
    - Performance timing helpers
    - Output to both file and console
    """

    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: int = logging.INFO
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually __name__)
            log_file: Optional file path for log output
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._context: Dict[str, Any] = {}

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create formatter
        formatter = StructuredFormatter()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _format_log(self, message: str, **kwargs) -> str:
        """Format log entry with context."""
        log_entry = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "level": kwargs.get("level", "INFO"),
            **self._context,
            **kwargs
        }
        return json.dumps(log_entry)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra={"kwargs": kwargs})

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra={"kwargs": kwargs})

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra={"kwargs": kwargs})

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra={"kwargs": kwargs})

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra={"kwargs": kwargs})

    @contextmanager
    def context(self, **kwargs):
        """
        Context manager for adding context to logs.

        Usage:
            with logger.context(operation="compile", document_id="123"):
                logger.info("Processing document")
        """
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield self
        finally:
            self._context = old_context

    @contextmanager
    def measure_time(self, operation: str):
        """
        Context manager for measuring operation time.

        Usage:
            with logger.measure_time("document_processing"):
                process_document()
        """
        import time
        start = time.time()
        self.info(f"Started: {operation}")
        try:
            yield
        finally:
            duration = time.time() - start
            self.info(
                f"Completed: {operation}",
                operation=operation,
                duration_seconds=duration
            )


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra kwargs from StructuredLogger
        if hasattr(record, "kwargs"):
            log_entry.update(record.kwargs)

        return json.dumps(log_entry)


def get_logger(name: str, log_file: Optional[str] = None) -> StructuredLogger:
    """
    Get or create a structured logger.

    Args:
        name: Logger name
        log_file: Optional log file path

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, log_file=log_file)
