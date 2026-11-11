"""End-to-end hybrid retrieval engine for ClauseLens.

Orchestrates dense semantic search, sparse lexical BM25 search,
Reciprocal Rank Fusion (RRF), and Cross-Encoder reranking into a unified pipeline.
"""

import logging
import time

from backend.src.config import get_settings
from backend.src.exceptions import RetrievalError
from backend.src.indexing.index_manager import IndexManager, get_shared_index_manager
from backend.src.retrieval.reranker import CrossEncoderReranker
from backend.src.retrieval.rrf import compute_rrf
from backend.src.schemas.query import RetrievalTelemetry, ScoredChunk

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Production two-stage hybrid retriever with RRF and Cross-Encoder reranking."""

    def __init__(
        self,
        index_manager: IndexManager | None = None,
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        """Initialize the hybrid retriever with index manager and reranker."""
        self.settings = get_settings()
        self.index_manager = index_manager or get_shared_index_manager()
        self.reranker = reranker or CrossEncoderReranker()

    def retrieve(
        self,
        query: str,
        doc_ids: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[ScoredChunk]:
        """Execute end-to-end hybrid search and cross-encoder reranking.

        Pipeline Stages:
        1. Dense Vector Search (ChromaDB) -> Top-K_dense (25)
        2. Sparse Lexical Search (BM25)  -> Top-K_sparse (25)
        3. Reciprocal Rank Fusion (RRF) -> Top-N_rerank (15)
        4. Cross-Encoder Reranker        -> Top-K_final (5)

        Args:
            query: User search query or question.
            doc_ids: Optional list of document IDs to scope retrieval.
            top_k: Override for final top-k returned chunks (defaults to settings.top_k_final).

        Returns:
            List of ScoredChunk instances with complete retrieval telemetry.

        Raises:
            RetrievalError: If retrieval or reranking fails.
        """
        start_time = time.perf_counter()
        final_k = top_k or self.settings.top_k_final

        try:
            # Ensure in-memory BM25 store reflects latest on-disk changes
            self.index_manager.reload_sparse_store_if_needed()

            logger.info("Executing hybrid search for query: '%s' (doc_scope=%s)", query, doc_ids)

            # Stage 1: Dense Vector Retrieval
            dense_results = self.index_manager.dense_store.search(
                query=query,
                top_k=self.settings.top_k_dense,
                doc_ids=doc_ids,
            )

            # Stage 2: Sparse BM25 Keyword Retrieval
            sparse_results = self.index_manager.sparse_store.search(
                query=query,
                top_k=self.settings.top_k_sparse,
                doc_ids=doc_ids,
            )

            if not dense_results and not sparse_results:
                logger.warning("No candidate chunks found in dense or sparse indices for query '%s'", query)
                return []

            # Stage 3: Reciprocal Rank Fusion (RRF)
            fused_candidates = compute_rrf(
                dense_results=dense_results,
                sparse_results=sparse_results,
                k=self.settings.rrf_k,
            )

            # Take Top-N candidates for reranking
            top_fused = fused_candidates[: self.settings.top_n_rerank]

            # Resolve full DocumentChunk objects for each fused candidate
            candidate_chunks: list[ScoredChunk] = []
            for candidate in top_fused:
                chunk = self.index_manager.get_chunk(candidate.chunk_id)
                if not chunk:
                    logger.warning("Chunk %s was ranked by RRF but not found in storage", candidate.chunk_id)
                    continue

                candidate_chunks.append(
                    ScoredChunk(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        filename=chunk.filename,
                        page_number=chunk.page_number,
                        section_path=chunk.section_path,
                        raw_content=chunk.raw_content,
                        contextualized_content=chunk.contextualized_content,
                        bounding_box=chunk.bounding_box,
                        telemetry=candidate.to_telemetry(),
                    )
                )

            # Stage 4: Cross-Encoder Reranking
            final_chunks = self.reranker.rerank(
                query=query,
                candidates=candidate_chunks,
                top_k=final_k,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                "Hybrid retrieval completed in %.2f ms: Dense=%d, Sparse=%d, RRF=%d, Final=%d",
                elapsed_ms,
                len(dense_results),
                len(sparse_results),
                len(top_fused),
                len(final_chunks),
            )
            return final_chunks

        except Exception as exc:
            logger.exception("Hybrid retrieval failed for query '%s'", query)
            raise RetrievalError(f"Hybrid retrieval error: {exc}") from exc

