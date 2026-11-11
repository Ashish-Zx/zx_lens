"""BM25 Sparse Keyword Store for ClauseLens.

Provides exact lexical retrieval with a specialized legal/financial tokenizer
that preserves section numbers (e.g., 11.4(b)), hyphenated terms (e.g., SOC-2),
and currency/percentage expressions, with atomic disk persistence.
"""

from collections.abc import Iterable
import json
import logging
from pathlib import Path
import pickle
import re
from typing import Any

from rank_bm25 import BM25Plus

from backend.src.exceptions import RetrievalError
from backend.src.schemas.document import DocumentChunk

logger = logging.getLogger(__name__)

# Specialized regex to preserve legal section numbers, currencies, percentages, and hyphenated terms
LEGAL_TOKEN_PATTERN = re.compile(
    r"""
    \$\d+(?:,\d+)*(?:\.\d+)?        # Currency amounts: $1,000, $50.00
    |\d+(?:\.\d+)*(?:\([a-zA-Z0-9]+\))+ # Section codes: 11.4(b), 8.3.1(a)(ii)
    |\d+(?:\.\d+)?%                 # Percentages: 99.9%, 15%
    |[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+ # Hyphenated terms: SOC-2, non-compete
    |\b\w+\b                         # Standard words
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Standard minimal legal stopword set (avoids removing identifiers)
ENGLISH_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with",
}


def legal_tokenizer(text: str) -> list[str]:
    """Tokenize legal/financial text while preserving key domain identifiers.

    Args:
        text: Input raw or contextualized text.

    Returns:
        List of normalized lowercase tokens preserving section numbers and compound words.
    """
    raw_tokens = LEGAL_TOKEN_PATTERN.findall(text)
    tokens: list[str] = []
    for token in raw_tokens:
        clean = token.strip()
        lowered = clean.lower()
        if lowered not in ENGLISH_STOPWORDS and len(clean) > 0:
            tokens.append(lowered)
    return tokens


class SparseBM25Store:
    """In-memory and disk-persisted BM25 keyword store."""

    def __init__(self) -> None:
        """Initialize an empty BM25 store."""
        self._chunks: dict[str, DocumentChunk] = {}
        self._corpus_ids: list[str] = []
        self._tokenized_corpus: list[list[str]] = []
        self._bm25: BM25Plus | None = None

    @property
    def total_chunks(self) -> int:
        """Return the total number of indexed chunks."""
        return len(self._chunks)

    def add_chunks(self, chunks: Iterable[DocumentChunk]) -> None:
        """Add and index document chunks.

        Args:
            chunks: Sequence of DocumentChunk instances to add.
        """
        new_chunks = list(chunks)
        if not new_chunks:
            return

        for chunk in new_chunks:
            if chunk.chunk_id in self._chunks:
                idx = self._corpus_ids.index(chunk.chunk_id)
                self._chunks[chunk.chunk_id] = chunk
                self._tokenized_corpus[idx] = legal_tokenizer(chunk.contextualized_content)
            else:
                self._chunks[chunk.chunk_id] = chunk
                self._corpus_ids.append(chunk.chunk_id)
                tokens = legal_tokenizer(chunk.contextualized_content)
                self._tokenized_corpus.append(tokens)

        # Re-initialize BM25Plus model with updated corpus
        self._bm25 = BM25Plus(self._tokenized_corpus)
        logger.info(
            "Indexed %d chunks into SparseBM25Store (total indexed: %d)",
            len(new_chunks),
            len(self._chunks),
        )

    def search(
        self,
        query: str,
        top_k: int = 25,
        doc_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        """Search the BM25 index with a query string.

        Args:
            query: User search or question text.
            top_k: Maximum number of results to return.
            doc_ids: Optional list of doc_ids to restrict search.

        Returns:
            List of (chunk_id, bm25_score) tuples sorted descending by score.
        """
        if not self._bm25 or not self._corpus_ids:
            return []

        query_tokens = legal_tokenizer(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        doc_ids_set = set(doc_ids) if doc_ids else None
        query_set = set(query_tokens)

        scored_candidates: list[tuple[str, float]] = []
        for chunk_id, tokens, score in zip(self._corpus_ids, self._tokenized_corpus, scores):
            # Only include if score > 0 and chunk shares at least one query token
            if score <= 0.0 or not query_set.intersection(tokens):
                continue

            if doc_ids_set is not None:
                chunk = self._chunks.get(chunk_id)
                if not chunk or chunk.doc_id not in doc_ids_set:
                    continue

            scored_candidates.append((chunk_id, float(score)))

        # Sort descending by score and slice top_k
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_k]

    def get_chunk(self, chunk_id: str) -> DocumentChunk | None:
        """Retrieve a chunk by its unique ID."""
        return self._chunks.get(chunk_id)

    def save(self, persist_dir: Path | str) -> None:
        """Persist the BM25 index and chunk metadata atomically to disk."""
        target_dir = Path(persist_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        data_payload = {
            "chunks": {cid: chunk.model_dump() for cid, chunk in self._chunks.items()},
            "corpus_ids": self._corpus_ids,
            "tokenized_corpus": self._tokenized_corpus,
        }

        temp_file = target_dir / "bm25_store.tmp"
        final_file = target_dir / "bm25_store.pkl"

        try:
            with temp_file.open("wb") as f:
                pickle.dump(data_payload, f, protocol=pickle.HIGHEST_PROTOCOL)
            temp_file.replace(final_file)
            logger.info("Successfully persisted BM25 store (%d chunks) to %s", len(self._chunks), final_file)
        except Exception as exc:
            if temp_file.exists():
                temp_file.unlink()
            raise RetrievalError(f"Failed to persist BM25 store to {final_file}: {exc}") from exc

    def load(self, persist_dir: Path | str) -> None:
        """Load the BM25 index from disk."""
        target_dir = Path(persist_dir).resolve()
        final_file = target_dir / "bm25_store.pkl"

        if not final_file.exists():
            logger.warning("BM25 persistence file does not exist: %s. Initializing empty store.", final_file)
            return

        try:
            with final_file.open("rb") as f:
                payload = pickle.load(f)

            self._chunks = {
                cid: DocumentChunk(**chunk_data)
                for cid, chunk_data in payload.get("chunks", {}).items()
            }
            self._corpus_ids = payload.get("corpus_ids", [])
            self._tokenized_corpus = payload.get("tokenized_corpus", [])

            if self._tokenized_corpus:
                self._bm25 = BM25Plus(self._tokenized_corpus)
            else:
                self._bm25 = None

            logger.info("Successfully loaded BM25 store (%d chunks) from %s", len(self._chunks), final_file)
        except Exception as exc:
            raise RetrievalError(f"Failed to load BM25 store from {final_file}: {exc}") from exc



