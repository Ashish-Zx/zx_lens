"""Reciprocal Rank Fusion (RRF) algorithm for ClauseLens hybrid search.

Merges ranked candidate lists from dense semantic search and sparse lexical search
using the formula: RRF_Score(d) = sum(1 / (k + rank_m(d))), with 1-indexed ranks.
"""

import logging
from typing import Any
from backend.src.schemas.query import RetrievalTelemetry

logger = logging.getLogger(__name__)


class RankedCandidate:
    """Intermediate candidate holding scores from dense and sparse retrieval stages."""

    def __init__(
        self,
        chunk_id: str,
        dense_rank: int | None = None,
        sparse_rank: int | None = None,
        dense_score: float | None = None,
        sparse_score: float | None = None,
        rrf_score: float = 0.0,
    ) -> None:
        self.chunk_id = chunk_id
        self.dense_rank = dense_rank
        self.sparse_rank = sparse_rank
        self.dense_score = dense_score
        self.sparse_score = sparse_score
        self.rrf_score = rrf_score

    def to_telemetry(self) -> RetrievalTelemetry:
        """Convert to Pydantic RetrievalTelemetry schema."""
        return RetrievalTelemetry(
            chunk_id=self.chunk_id,
            dense_rank=self.dense_rank,
            bm25_rank=self.sparse_rank,
            dense_score=self.dense_score,
            bm25_score=self.sparse_score,
            rrf_score=self.rrf_score,
            reranker_score=None,
        )


def compute_rrf(
    dense_results: list[tuple[str, float]],
    sparse_results: list[tuple[str, float]],
    k: int = 60,
) -> list[RankedCandidate]:
    """Compute Reciprocal Rank Fusion scores across dense and sparse ranked lists.

    Args:
        dense_results: Ordered list of (chunk_id, score) from dense vector search.
        sparse_results: Ordered list of (chunk_id, score) from sparse BM25 search.
        k: Smoothing constant (default 60, per Cormack et al. / enterprise standard).

    Returns:
        List of RankedCandidate objects sorted by rrf_score in descending order.
    """
    candidates: dict[str, RankedCandidate] = {}

    # Process Dense Search ranks (1-indexed)
    for rank_0, (chunk_id, score) in enumerate(dense_results):
        dense_rank_1 = rank_0 + 1
        rrf_contribution = 1.0 / (k + dense_rank_1)

        if chunk_id not in candidates:
            candidates[chunk_id] = RankedCandidate(
                chunk_id=chunk_id,
                dense_rank=dense_rank_1,
                dense_score=score,
                rrf_score=rrf_contribution,
            )
        else:
            cand = candidates[chunk_id]
            cand.dense_rank = dense_rank_1
            cand.dense_score = score
            cand.rrf_score += rrf_contribution

    # Process Sparse Search ranks (1-indexed)
    for rank_0, (chunk_id, score) in enumerate(sparse_results):
        sparse_rank_1 = rank_0 + 1
        rrf_contribution = 1.0 / (k + sparse_rank_1)

        if chunk_id not in candidates:
            candidates[chunk_id] = RankedCandidate(
                chunk_id=chunk_id,
                sparse_rank=sparse_rank_1,
                sparse_score=score,
                rrf_score=rrf_contribution,
            )
        else:
            cand = candidates[chunk_id]
            cand.sparse_rank = sparse_rank_1
            cand.sparse_score = score
            cand.rrf_score += rrf_contribution

    # Sort all candidates descending by rrf_score
    sorted_candidates = sorted(
        candidates.values(),
        key=lambda c: c.rrf_score,
        reverse=True,
    )

    logger.debug(
        "RRF fused %d dense and %d sparse results into %d unique candidates (k=%d)",
        len(dense_results),
        len(sparse_results),
        len(sorted_candidates),
        k,
    )
    return sorted_candidates

