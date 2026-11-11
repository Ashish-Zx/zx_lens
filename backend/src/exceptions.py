"""Custom domain exceptions for ClauseLens.

Provides specific, structured exceptions across all pipeline stages
(parsing, indexing, retrieval, generation).
"""


class ClauseLensError(Exception):
    """Base exception class for all ClauseLens domain errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentParsingError(ClauseLensError):
    """Raised when Docling fails to parse a document layout or extract tables."""
    pass


class IndexSyncError(ClauseLensError):
    """Raised when synchronization between dense and sparse indices fails."""
    pass


class RetrievalError(ClauseLensError):
    """Raised when hybrid search, RRF calculation, or reranking fails."""
    pass


class GenerationError(ClauseLensError):
    """Raised when LLM synthesis or structured output parsing fails."""
    pass

