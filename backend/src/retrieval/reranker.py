"""Cross-Encoder reranking module for ClauseLens.

Performs joint (query, chunk_context) deep cross-attention scoring
using HuggingFace Cross-Encoder models (e.g., cross-encoder/ms-marco-MiniLM-L-6-v2),
refining the top RRF candidate pool into precision-ranked context chunks.
"""

import logging
from typing import Any

from sentence_transformers import CrossEncoder

from backend.src.config import get_settings
from backend.src.exceptions import RetrievalError
from backend.src.schemas.query import ScoredChunk

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Production Cross-Encoder reranker scoring query-context pairs jointly."""

    def __init__(self, model_name: str | None = None) -> None:
        """Initialize the cross-encoder model.

        Args:
            model_name: Hugging Face model identifier for the cross-encoder.
        """
        app_settings = get_settings()
        self.model_name = model_name or app_settings.reranker_model_name
        logger.info("Initializing CrossEncoderReranker with model: %s", self.model_name)

        try:
            self._model = CrossEncoder(self.model_name)
        except Exception as exc:
            raise RetrievalError(
                f"Failed to load Cross-Encoder model '{self.model_name}': {exc}"
            ) from exc

    def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Score (query, chunk_context) pairs jointly and return top-k candidates.

        Args:
            query: The user query string.
            candidates: Intermediate fused candidates from RRF.
            top_k: Number of final chunks to return.

        Returns:
            List of ScoredChunk instances sorted descending by reranker_score.

        Raises:
            RetrievalError: If reranking inference fails.
        """
        if not candidates:
            return []

        # Retain full contextualized content (including Document and Section breadcrumbs)
        pairs = [
            (query, candidate.contextualized_content)
            for candidate in candidates
        ]

        try:
            logger.debug("Reranking %d candidates with Cross-Encoder...", len(pairs))
            scores = self._model.predict(pairs)

            # Assign reranker_score into telemetry of each ScoredChunk
            scored_list: list[tuple[float, ScoredChunk]] = []
            for candidate, score in zip(candidates, scores):
                candidate.telemetry = candidate.telemetry.model_copy(
                    update={"reranker_score": float(score)}
                )
                scored_list.append((float(score), candidate))

            # Sort descending by cross-encoder score
            scored_list.sort(key=lambda x: x[0], reverse=True)
            top_results = [cand for _, cand in scored_list[:top_k]]

            logger.info(
                "Reranked %d candidates to top %d (top score: %.4f)",
                len(candidates),
                len(top_results),
                top_results[0].telemetry.reranker_score if top_results else 0.0,
            )
            return top_results

        except Exception as exc:
            logger.exception("Cross-Encoder reranking failed for query: '%s'", query)
            raise RetrievalError(f"Reranking failed: {exc}") from exc

