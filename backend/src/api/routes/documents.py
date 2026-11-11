"""FastAPI router for document ingestion, parsing, and chunk management."""

import hashlib
import logging
from pathlib import Path
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from backend.src.exceptions import DocumentParsingError, IndexSyncError
from backend.src.ingestion.contextual_chunker import ContextualChunker
from backend.src.ingestion.docling_parser import DoclingParser
from backend.src.indexing.index_manager import IndexManager, get_shared_index_manager
from backend.src.schemas.document import DocumentChunk, ElementType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Singletons for API handlers (lazily initialized)
_parser: DoclingParser | None = None
_chunker: ContextualChunker | None = None
_index_manager: IndexManager | None = None


def get_parser() -> DoclingParser:
    global _parser
    if _parser is None:
        _parser = DoclingParser()
    return _parser


def get_chunker() -> ContextualChunker:
    global _chunker
    if _chunker is None:
        _chunker = ContextualChunker()
    return _chunker


def get_index_manager() -> IndexManager:
    return get_shared_index_manager()


class IngestionResponse(BaseModel):
    """Response returned upon successful document upload and dual indexing."""

    doc_id: str = Field(..., description="Unique SHA-256 document identifier")
    filename: str = Field(..., description="Uploaded file name")
    page_count: int = Field(..., description="Number of parsed pages")
    chunk_count: int = Field(..., description="Number of generated contextual chunks")
    table_count: int = Field(..., description="Number of extracted tabular structures")
    status: str = Field(default="indexed", description="Ingestion processing status")


class DocumentSummary(BaseModel):
    """Aggregated summary of a single indexed document."""

    doc_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    chunk_count: int = Field(..., ge=0, description="Number of indexed chunks")
    page_count: int = Field(..., ge=0, description="Number of unique pages spanned")
    pages: list[int] = Field(default_factory=list, description="Sorted page numbers")
    element_types: list[str] = Field(
        default_factory=list,
        description="Distinct element types (text, table, ...)",
    )


@router.post(
    "/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload, parse with Docling, and dual-index a PDF contract",
)
async def upload_document(
    file: UploadFile = File(..., description="Target PDF document file"),
) -> IngestionResponse:
    """Ingest a PDF file: layout parsing with Docling, breadcrumb chunking, and dual indexing."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported for layout-aware ingestion.",
        )

    # Save uploaded file to raw data directory
    raw_dir = Path("backend/data/raw").resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)
    temp_path = raw_dir / file.filename

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_bytes = temp_path.read_bytes()
        doc_id = hashlib.sha256(file_bytes).hexdigest()[:16]

        logger.info("Parsing document %s with Docling (doc_id=%s)", file.filename, doc_id)
        parser = get_parser()
        parsed_doc = parser.parse_pdf(file_path=temp_path, doc_id=doc_id)

        # Contextual boundary chunking
        chunker = get_chunker()
        chunks = chunker.chunk_document(parsed_doc)

        table_count = sum(1 for c in chunks if c.element_type == ElementType.TABLE)

        # Atomic dual indexing into ChromaDB and BM25
        index_manager = get_index_manager()
        index_manager.index_chunks(chunks)

        return IngestionResponse(
            doc_id=doc_id,
            filename=file.filename,
            page_count=parsed_doc.metadata.page_count,
            chunk_count=len(chunks),
            table_count=table_count,
            status="indexed",
        )

    except DocumentParsingError as exc:
        logger.exception("Docling parsing error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document parsing error: {exc.message}",
        ) from exc
    except IndexSyncError as exc:
        logger.exception("Dual index sync error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dual index synchronization error: {exc.message}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during document ingestion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        ) from exc


@router.get(
    "/stats",
    summary="Get dual-index statistics",
)
def get_index_statistics() -> dict[str, int]:
    """Return count of vectors and keyword chunks in storage."""
    return get_index_manager().stats()


@router.get(
    "/list",
    response_model=list[DocumentSummary],
    summary="List all indexed documents",
)
def list_indexed_documents() -> list[DocumentSummary]:
    """Return aggregated summaries for every distinct indexed document."""
    return [
        DocumentSummary(**entry)
        for entry in get_index_manager().list_documents()
    ]


@router.get(
    "/{chunk_id}",
    response_model=DocumentChunk,
    summary="Inspect a specific chunk by its chunk_id",
)
def get_chunk_by_id(chunk_id: str) -> DocumentChunk:
    """Retrieve full chunk metadata, breadcrumbs, and bounding box for a chunk ID."""
    chunk = get_index_manager().get_chunk(chunk_id)
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk with ID '{chunk_id}' was not found.",
        )
    return chunk

