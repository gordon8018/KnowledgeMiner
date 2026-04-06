"""
Centralized exception hierarchy for Knowledge Compiler.

This module defines custom exceptions that provide:
1. Clear categorization of error types
2. Consistent error handling across the codebase
3. Better debugging and error reporting
4. Type-safe exception catching

Usage:
    try:
        some_operation()
    except KnowledgeCompilerError as e:
        # Handle any Knowledge Compiler specific error
        logger.error(f"Knowledge Compiler error: {e}")
    except DocumentNotFoundError:
        # Handle specific document error
        logger.error(f"Document not found: {e.document_path}")
"""


class KnowledgeCompilerError(Exception):
    """Base exception for all Knowledge Compiler errors.

    All custom exceptions should inherit from this class to allow
    catching all Knowledge Compiler specific errors with a single
    except clause.
    """

    def __init__(self, message: str, details: dict = None):
        """Initialize Knowledge Compiler error.

        Args:
            message: Human-readable error message
            details: Additional error context (optional)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """Return formatted error message."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# Document and File Errors

class DocumentError(KnowledgeCompilerError):
    """Base class for document-related errors."""

    def __init__(self, message: str, document_path: str = None, details: dict = None):
        """Initialize document error.

        Args:
            message: Human-readable error message
            document_path: Path to the document that caused the error
            details: Additional error context
        """
        super().__init__(message, details)
        self.document_path = document_path


class DocumentNotFoundError(DocumentError):
    """Raised when a document cannot be found."""

    def __init__(self, document_path: str):
        super().__init__(
            f"Document not found: {document_path}",
            document_path=document_path
        )


class DocumentParseError(DocumentError):
    """Raised when a document cannot be parsed."""

    def __init__(self, document_path: str, parse_error: str = None):
        details = {"parse_error": parse_error} if parse_error else None
        super().__init__(
            f"Failed to parse document: {document_path}",
            document_path=document_path,
            details=details
        )


class DocumentValidationError(DocumentError):
    """Raised when a document fails validation."""

    def __init__(self, document_path: str, validation_errors: list = None):
        details = {"validation_errors": validation_errors} if validation_errors else None
        super().__init__(
            f"Document validation failed: {document_path}",
            document_path=document_path,
            details=details
        )


# Configuration Errors

class ConfigurationError(KnowledgeCompilerError):
    """Base class for configuration-related errors."""

    def __init__(self, message: str, config_key: str = None, details: dict = None):
        """Initialize configuration error.

        Args:
            message: Human-readable error message
            config_key: Configuration key that caused the error
            details: Additional error context
        """
        super().__init__(message, details)
        self.config_key = config_key


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    def __init__(self, message: str, config_key: str = None, validation_errors: list = None):
        details = {"validation_errors": validation_errors} if validation_errors else None
        super().__init__(
            message,
            config_key=config_key,
            details=details
        )


class ConfigNotFoundError(ConfigurationError):
    """Raised when configuration file is not found."""

    def __init__(self, config_path: str):
        super().__init__(
            f"Configuration file not found: {config_path}",
            details={"config_path": config_path}
        )


# Concept and Knowledge Errors

class ConceptError(KnowledgeCompilerError):
    """Base class for concept-related errors."""

    def __init__(self, message: str, concept_name: str = None, details: dict = None):
        """Initialize concept error.

        Args:
            message: Human-readable error message
            concept_name: Name of the concept that caused the error
            details: Additional error context
        """
        super().__init__(message, details)
        self.concept_name = concept_name


class ConceptNotFoundError(ConceptError):
    """Raised when a concept cannot be found."""

    def __init__(self, concept_name: str):
        super().__init__(
            f"Concept not found: {concept_name}",
            concept_name=concept_name
        )


class ConceptValidationError(ConceptError):
    """Raised when a concept fails validation."""

    def __init__(self, concept_name: str, validation_errors: list = None):
        details = {"validation_errors": validation_errors} if validation_errors else None
        super().__init__(
            f"Concept validation failed: {concept_name}",
            concept_name=concept_name,
            details=details
        )


# LLM and API Errors

class LLMError(KnowledgeCompilerError):
    """Base class for LLM-related errors."""

    def __init__(self, message: str, provider: str = None, details: dict = None):
        """Initialize LLM error.

        Args:
            message: Human-readable error message
            provider: LLM provider that caused the error
            details: Additional error context
        """
        super().__init__(message, details)
        self.provider = provider


class LLMProviderError(LLMError):
    """Raised when LLM provider initialization fails."""

    def __init__(self, provider: str, reason: str = None):
        message = f"Failed to initialize LLM provider: {provider}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, provider=provider)


class LLMRateLimitError(LLMError):
    """Raised when LLM API rate limit is exceeded."""

    def __init__(self, provider: str, retry_after: int = None):
        details = {"retry_after": retry_after} if retry_after else None
        super().__init__(
            f"LLM rate limit exceeded for provider: {provider}",
            provider=provider,
            details=details
        )


class LLMTimeoutError(LLMError):
    """Raised when LLM API request times out."""

    def __init__(self, provider: str, timeout: int = None):
        details = {"timeout": timeout} if timeout else None
        super().__init__(
            f"LLM request timeout for provider: {provider}",
            provider=provider,
            details=details
        )


# Processing and Pipeline Errors

class ProcessingError(KnowledgeCompilerError):
    """Base class for processing-related errors."""

    def __init__(self, message: str, stage: str = None, details: dict = None):
        """Initialize processing error.

        Args:
            message: Human-readable error message
            stage: Processing stage where error occurred
            details: Additional error context
        """
        super().__init__(message, details)
        self.stage = stage


class ExtractionError(ProcessingError):
    """Raised when information extraction fails."""

    def __init__(self, message: str, source: str = None, details: dict = None):
        details = details or {}
        if source:
            details["source"] = source
        super().__init__(
            message,
            stage="extraction",
            details=details
        )
        self.source = source


class GenerationError(ProcessingError):
    """Raised when content generation fails."""

    def __init__(self, message: str, generator_type: str = None, details: dict = None):
        details = details or {}
        if generator_type:
            details["generator_type"] = generator_type
        super().__init__(
            message,
            stage="generation",
            details=details
        )
        self.generator_type = generator_type


# Index and Storage Errors

class StorageError(KnowledgeCompilerError):
    """Base class for storage-related errors."""

    def __init__(self, message: str, storage_path: str = None, details: dict = None):
        """Initialize storage error.

        Args:
            message: Human-readable error message
            storage_path: Path related to the storage error
            details: Additional error context
        """
        super().__init__(message, details)
        self.storage_path = storage_path


class IndexNotFoundError(StorageError):
    """Raised when an index cannot be found."""

    def __init__(self, index_path: str):
        super().__init__(
            f"Index not found: {index_path}",
            storage_path=index_path
        )


class IndexValidationError(StorageError):
    """Raised when an index fails validation."""

    def __init__(self, index_path: str, validation_errors: list = None):
        details = {"validation_errors": validation_errors} if validation_errors else None
        super().__init__(
            f"Index validation failed: {index_path}",
            storage_path=index_path,
            details=details
        )


# Discovery and Analysis Errors

class DiscoveryError(KnowledgeCompilerError):
    """Base class for discovery-related errors."""

    def __init__(self, message: str, discovery_type: str = None, details: dict = None):
        """Initialize discovery error.

        Args:
            message: Human-readable error message
            discovery_type: Type of discovery operation that failed
            details: Additional error context
        """
        super().__init__(message, details)
        self.discovery_type = discovery_type


class RelationMiningError(DiscoveryError):
    """Raised when relation mining fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message,
            discovery_type="relation_mining",
            details=details
        )


class PatternDetectionError(DiscoveryError):
    """Raised when pattern detection fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message,
            discovery_type="pattern_detection",
            details=details
        )


class GapAnalysisError(DiscoveryError):
    """Raised when gap analysis fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message,
            discovery_type="gap_analysis",
            details=details
        )


# Utility functions for error handling

def format_error(error: Exception) -> str:
    """Format an exception for logging or display.

    Args:
        error: Exception to format

    Returns:
        Formatted error message string
    """
    if isinstance(error, KnowledgeCompilerError):
        return str(error)
    else:
        return f"{type(error).__name__}: {str(error)}"


def get_error_context(error: Exception) -> dict:
    """Extract structured context from an exception.

    Args:
        error: Exception to extract context from

    Returns:
        Dictionary with error context
    """
    if isinstance(error, KnowledgeCompilerError):
        context = {
            "error_type": type(error).__name__,
            "message": error.message,
            "details": error.details
        }
        # Add specific fields based on error type
        if isinstance(error, DocumentError) and error.document_path:
            context["document_path"] = error.document_path
        elif isinstance(error, ConceptError) and error.concept_name:
            context["concept_name"] = error.concept_name
        elif isinstance(error, LLMError) and error.provider:
            context["provider"] = error.provider
        elif isinstance(error, ProcessingError) and error.stage:
            context["stage"] = error.stage
        return context
    else:
        return {
            "error_type": type(error).__name__,
            "message": str(error)
        }