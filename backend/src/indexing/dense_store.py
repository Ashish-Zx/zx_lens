"""ChromaDB dense vector store wrapper for ClauseLens.

Embeds contextualized chunks using sentence-transformers (BAAI/bge-small-en-v1.5),
indexes vectors into ChromaDB with metadata filtering, and returns scored matches.
"""

from collections.abc import Iterable
import json
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from backend.src.config import get_settings
from backend.src.exceptions import RetrievalError
from backend.src.schemas.document import (
    BoundingBox,
    DocumentChunk,
    ElementType,
)

logger = logging.getLogger(__name__)


class DenseChromaStore:
    """Production ChromaDB wrapper managing vector indexing and semantic retrieval."""

    def __init__(
        self,
        persist_dir: Path | str | None = None,
        model_name: str | None = None,
        collection_name: str = "clauselens_chunks",
    ) -> None:
        """Initialize ChromaDB client and local embedding model.

        Args:
            persist_dir: Directory where ChromaDB sqlite/parquet files are stored.
            model_name: Hugging Face model identifier for sentence embeddings.
            collection_name: Target Chroma collection name.
        """
        app_settings = get_settings()
        self.persist_dir = Path(persist_dir or app_settings.chroma_persist_dir).resolve()
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name or app_settings.embedding_model_name
        self.collection_name = collection_name

        logger.info(
            "Initializing DenseChromaStore at %s with embedding model %s",
            self.persist_dir,
            self.model_name,
        )

        try:
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._embedder = SentenceTransformer(self.model_name)
        except Exception as exc:
            raise RetrievalError(
                f"Failed to initialize ChromaDB or embedding model {self.model_name}: {exc}"
            ) from exc

    @property
    def total_chunks(self) -> int:
        """Return total number of vectors in the collection."""
        return self._collection.count()

    def add_chunks(self, chunks: Iterable[DocumentChunk]) -> None:
        """Embed and upsert chunks into ChromaDB with provenance metadata.

        Args:
            chunks: Sequence of DocumentChunk instances to index.
        """
        chunk_list = list(chunks)
        if not chunk_list:
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunk_list:
            ids.append(chunk.chunk_id)
            # Embed the contextualized content to leverage document & section breadcrumbs
            documents.append(chunk.contextualized_content)

            bbox_json = chunk.bounding_box.model_dump_json() if chunk.bounding_box else ""
            metadatas.append(
                {
                    "doc_id": chunk.doc_id,
                    "filename": chunk.filename,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "element_type": chunk.element_type.value,
                    "section_path": chunk.section_path,
                    "raw_content": chunk.raw_content,
                    "bounding_box": bbox_json,
                }
            )

        try:
            logger.info("Computing dense embeddings for %d chunks...", len(documents))
            embeddings = self._embedder.encode(
                documents,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ).tolist()

            self._collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info(
                "Upserted %d vectors into Chroma collection '%s' (total: %d)",
                len(ids),
                self.collection_name,
                self._collection.count(),
            )
        except Exception as exc:
            raise RetrievalError(f"Failed to embed or upsert chunks into ChromaDB: {exc}") from exc

    def search(
        self,
        query: str,
        top_k: int = 25,
        doc_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        """Perform semantic dense search with optional document scoping.

        Args:
            query: User search text or question.
            top_k: Number of nearest neighbors to retrieve.
            doc_ids: Optional list of doc_ids to scope the search.

        Returns:
            List of (chunk_id, similarity_score) sorted descending by similarity.
        """
        if self._collection.count() == 0:
            return []

        try:
            query_vector = self._embedder.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True,
            ).tolist()

            # Build metadata filter
            where_filter: dict[str, Any] | None = None
            if doc_ids:
                if len(doc_ids) == 1:
                    where_filter = {"doc_id": doc_ids[0]}
                else:
                    where_filter = {"doc_id": {"$in": doc_ids}}

            results = self._collection.query(
                query_embeddings=query_vector,
                n_results=min(top_k, self._collection.count()),
                where=where_filter,
                include=["distances", "metadatas"],
            )

            scored_candidates: list[tuple[str, float]] = []
            retrieved_ids = results.get("ids", [[]])[0]
            retrieved_dists = results.get("distances", [[]])[0]

            for cid, dist in zip(retrieved_ids, retrieved_dists):
                # Cosine distance to similarity: similarity = 1.0 - distance
                similarity = max(0.0, 1.0 - float(dist))
                scored_candidates.append((cid, similarity))

            return scored_candidates
        except Exception as exc:
            logger.exception("Chroma dense search failed for query '%s'", query)
            raise RetrievalError(f"Dense search failed: {exc}") from exc

    def get_chunk(self, chunk_id: str) -> DocumentChunk | None:
        """Retrieve a DocumentChunk by ID directly from Chroma."""
        try:
            res = self._collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas"],
            )
            ids = res.get("ids", [])
            if not ids:
                return None

            doc_text = res["documents"][0]
            meta = res["metadatas"][0]

            bbox_obj = None
            if meta.get("bounding_box"):
                bbox_obj = BoundingBox.model_validate_json(meta["bounding_box"])

            return DocumentChunk(
                chunk_id=chunk_id,
                doc_id=str(meta.get("doc_id", "")),
                filename=str(meta.get("filename", "")),
                page_number=int(meta.get("page_number", 1)),
                chunk_index=int(meta.get("chunk_index", 0)),
                element_type=ElementType(meta.get("element_type", ElementType.TEXT.value)),
                section_path=str(meta.get("section_path", "Root")),
                raw_content=str(meta.get("raw_content", doc_text)),
                contextualized_content=doc_text,
                bounding_box=bbox_obj,
            )
        except Exception as exc:
            logger.warning("Failed to retrieve chunk %s from Chroma: %s", chunk_id, exc)
            return None
