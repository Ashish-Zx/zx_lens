"""Query and response schemas for ClauseLens.

Defines Pydantic models for search requests, citations, retrieval telemetry,
and structured RAG synthesis responses.
"""

from pydantic import BaseModel, ConfigDict, Field
from backend.src.schemas.document import BoundingBox


class QueryRequest(BaseModel):
    """Incoming user query with optional document scoping."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(..., min_length=2, description="User search or question text")
    doc_ids: list[str] | None = Field(
        default=None,
        description="Optional list of doc_ids to filter the search space",
    )
    top_k: int | None = Field(
        default=None,
        description="Override default number of final chunks returned to generator",
    )


class RetrievalTelemetry(BaseModel):
    """Ranking positions and scores across retrieval stages for explainability."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(..., description="Target chunk identifier")
    dense_rank: int | None = Field(
        default=None,
        description="1-indexed rank in ChromaDB vector search",
    )
    bm25_rank: int | None = Field(
        default=None,
        description="1-indexed rank in BM25 keyword search",
    )
    dense_score: float | None = Field(
        default=None,
        description="Cosine similarity or distance score from dense search",
    )
    bm25_score: float | None = Field(
        default=None,
        description="BM25 TF-IDF relevance score",
    )
    rrf_score: float | None = Field(
        default=None,
        description="Reciprocal Rank Fusion score: 1 / (60 + rank)",
    )
    reranker_score: float | None = Field(
        default=None,
        description="Cross-Encoder logit score for (query, chunk)",
    )


class ScoredChunk(BaseModel):
    """Retrieved chunk bundled with its multi-stage telemetry."""

    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    section_path: str
    raw_content: str
    contextualized_content: str
    bounding_box: BoundingBox | None = None
    telemetry: RetrievalTelemetry


class Citation(BaseModel):
    """A grounded citation backing a factual claim in the generated answer."""

    model_config = ConfigDict(frozen=True)

    citation_id: int = Field(..., description="Numeric marker corresponding to [1], [2] in answer")
    chunk_id: str = Field(..., description="Source chunk ID")
    doc_name: str = Field(..., description="Filename of source document")
    page_number: int = Field(..., ge=1, description="Page number where quote appears")
    section_path: str = Field(..., description="Breadcrumb section hierarchy")
    verbatim_quote: str = Field(..., description="Exact supporting text excerpt")
    bounding_box: BoundingBox | None = Field(
        default=None,
        description="Bounding box for UI PDF highlight overlay",
    )


class RAGResponse(BaseModel):
    """Final grounded synthesis returned to API clients and UI."""

    query: str = Field(..., description="Original user query")
    answer: str = Field(
        ...,
        description="Synthesized markdown response with inline citations [1], [2]",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Grounded citations mapped to inline markers",
    )
    telemetry: list[RetrievalTelemetry] = Field(
        default_factory=list,
        description="Retrieval explainability telemetry for every evaluated chunk",
    )
    unanswerable_reason: str | None = Field(
        default=None,
        description="Explanation if the question cannot be answered from context",
    )
    total_latency_ms: float = Field(
        default=0.0,
        description="Total end-to-end request latency in milliseconds",
    )

