"""FastAPI router for hybrid retrieval and grounded Q&A."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from backend.src.exceptions import GenerationError, RetrievalError
from backend.src.generation.generator import GroundedGenerator
from backend.src.retrieval.hybrid_retriever import HybridRetriever
from backend.src.schemas.query import QueryRequest, RAGResponse, ScoredChunk

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

# Singletons for query routes
_retriever: HybridRetriever | None = None
_generator: GroundedGenerator | None = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


def get_generator() -> GroundedGenerator:
    global _generator
    if _generator is None:
        _generator = GroundedGenerator()
    return _generator


@router.post(
    "/search",
    response_model=list[ScoredChunk],
    summary="Execute hybrid search (Dense + BM25 + RRF + Cross-Encoder)",
)
def search_chunks(request: QueryRequest) -> list[ScoredChunk]:
    """Retrieve top precision-ranked chunks with multi-stage ranking telemetry."""
    try:
        retriever = get_retriever()
        return retriever.retrieve(
            query=request.query,
            doc_ids=request.doc_ids,
            top_k=request.top_k,
        )
    except RetrievalError as exc:
        logger.exception("Retrieval error in /search: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {exc.message}",
        ) from exc


@router.post(
    "/ask",
    response_model=RAGResponse,
    summary="Interactive contract Q&A with grounded citations and bounding boxes",
)
def ask_question(request: QueryRequest) -> RAGResponse:
    """Execute hybrid retrieval followed by zero-hallucination structured synthesis."""
    try:
        retriever = get_retriever()
        chunks = retriever.retrieve(
            query=request.query,
            doc_ids=request.doc_ids,
            top_k=request.top_k,
        )

        generator = get_generator()
        return generator.generate(
            query=request.query,
            retrieved_chunks=chunks,
        )
    except (RetrievalError, GenerationError) as exc:
        logger.exception("Error in /ask pipeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A pipeline failed: {exc.message}",
        ) from exc

