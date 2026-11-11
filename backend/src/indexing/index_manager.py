"""Dual-index synchronization manager for ClauseLens.

Coordinates atomic indexing across DenseChromaStore and SparseBM25Store,
guaranteeing deterministic chunk_id alignment and persistent state.
"""

from collections.abc import Iterable
import logging
from pathlib import Path

from backend.src.config import get_settings
from backend.src.exceptions import IndexSyncError
from backend.src.indexing.dense_store import DenseChromaStore
from backend.src.indexing.sparse_store import SparseBM25Store
from backend.src.schemas.document import DocumentChunk

logger = logging.getLogger(__name__)


class IndexManager:
    """Atomic dual-index synchronization manager."""

    def __init__(
        self,
        dense_store: DenseChromaStore | None = None,
        sparse_store: SparseBM25Store | None = None,
    ) -> None:
        """Initialize the manager with dense and sparse stores."""
        settings = get_settings()
        self.dense_store = dense_store or DenseChromaStore()
        self.sparse_store = sparse_store or SparseBM25Store()

        # Load persisted BM25 index from disk if present
        self.bm25_persist_dir = settings.bm25_persist_dir
        self.sparse_store.load(self.bm25_persist_dir)
        final_file = Path(self.bm25_persist_dir).resolve() / "bm25_store.pkl"
        self._last_bm25_mtime = final_file.stat().st_mtime if final_file.exists() else 0.0

        logger.info(
            "IndexManager ready: Dense vectors=%d, BM25 chunks=%d",
            self.dense_store.total_chunks,
            self.sparse_store.total_chunks,
        )

    def reload_sparse_store_if_needed(self) -> None:
        """Reload BM25 store if on-disk store has updated or in-memory is empty."""
        final_file = Path(self.bm25_persist_dir).resolve() / "bm25_store.pkl"
        if final_file.exists():
            mtime = final_file.stat().st_mtime
            if mtime > getattr(self, "_last_bm25_mtime", 0.0) or self.sparse_store.total_chunks == 0:
                logger.info("Reloading BM25 store from disk (mtime changed: %s > %s)", mtime, getattr(self, "_last_bm25_mtime", 0.0))
                self.sparse_store.load(self.bm25_persist_dir)
                self._last_bm25_mtime = mtime

    def index_chunks(self, chunks: Iterable[DocumentChunk]) -> None:
        """Atomically index chunks into both ChromaDB and BM25 stores.

        Args:
            chunks: Chunks to index.

        Raises:
            IndexSyncError: If writing to either index fails.
        """
        chunk_list = list(chunks)
        if not chunk_list:
            return

        logger.info("Synchronizing %d chunks across dual indices...", len(chunk_list))
        try:
            # 1. Index into ChromaDB dense store
            self.dense_store.add_chunks(chunk_list)

            # 2. Index into BM25 sparse store
            self.sparse_store.add_chunks(chunk_list)

            # 3. Atomically persist BM25 to disk
            self.sparse_store.save(self.bm25_persist_dir)

            logger.info(
                "Successfully synchronized %d chunks. Total: Dense=%d, Sparse=%d",
                len(chunk_list),
                self.dense_store.total_chunks,
                self.sparse_store.total_chunks,
            )
        except Exception as exc:
            logger.exception("Failed dual-index synchronization: %s", exc)
            raise IndexSyncError(
                f"Dual index synchronization failed: {exc}",
                details={"chunk_count": len(chunk_list), "error": str(exc)},
            ) from exc

    def get_chunk(self, chunk_id: str) -> DocumentChunk | None:
        """Retrieve chunk by ID, checking memory first then vector metadata."""
        chunk = self.sparse_store.get_chunk(chunk_id)
        if chunk is not None:
            return chunk
        return self.dense_store.get_chunk(chunk_id)

    def list_documents(self) -> list[dict[str, object]]:
        """Aggregate distinct indexed documents with chunk and page stats.

        Returns:
            List of dicts keyed by doc_id, each containing the representative
            filename, chunk count, page count, and document field coverage.
        """
        self.reload_sparse_store_if_needed()
        docs: dict[str, dict[str, object]] = {}

        for chunk_id in self.sparse_store._corpus_ids:
            chunk = self.sparse_store.get_chunk(chunk_id)
            if not chunk:
                continue
            entry = docs.setdefault(
                chunk.doc_id,
                {
                    "doc_id": chunk.doc_id,
                    "filename": chunk.filename,
                    "chunk_count": 0,
                    "pages": set(),
                    "element_types": set(),
                },
            )
            entry["chunk_count"] = int(entry["chunk_count"]) + 1  # type: ignore[operator]
            entry["pages"].add(chunk.page_number)  # type: ignore[attr-defined]
            entry["element_types"].add(chunk.element_type.value)  # type: ignore[attr-defined]

        for entry in docs.values():
            entry["pages"] = sorted(entry["pages"])  # type: ignore[arg-type]
            entry["page_count"] = len(entry["pages"])  # type: ignore[arg-type]
            entry["element_types"] = sorted(entry["element_types"])  # type: ignore[arg-type]

        return sorted(docs.values(), key=lambda d: str(d["filename"]).lower())

    def stats(self) -> dict[str, int]:
        """Return counts of indexed elements across stores."""
        self.reload_sparse_store_if_needed()
        return {
            "dense_count": self.dense_store.total_chunks,
            "sparse_count": self.sparse_store.total_chunks,
        }


_shared_index_manager: IndexManager | None = None


def get_shared_index_manager() -> IndexManager:
    """Return process-wide singleton IndexManager to prevent index divergence."""
    global _shared_index_manager
    if _shared_index_manager is None:
        _shared_index_manager = IndexManager()
    return _shared_index_manager
