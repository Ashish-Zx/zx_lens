"""Document and chunk schemas for ClauseLens.

Defines Pydantic models for bounding boxes, document metadata,
and layout-aware chunks with contextual breadcrumb provenance.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
from pydantic import BaseModel, ConfigDict, Field


class ElementType(str, Enum):
    """Types of layout elements recognized during document parsing."""

    TEXT = "text"
    TABLE = "table"
    SECTION_HEADER = "section_header"
    LIST_ITEM = "list_item"


class BoundingBox(BaseModel):
    """Coordinate bounding box on a document page for frontend highlighting."""

    model_config = ConfigDict(frozen=True)

    l: float = Field(..., description="Left x-coordinate")
    t: float = Field(..., description="Top y-coordinate")
    r: float = Field(..., description="Right x-coordinate")
    b: float = Field(..., description="Bottom y-coordinate")
    page_number: int = Field(..., ge=1, description="1-indexed page number")
    coord_origin: str = Field(
        default="TOPLEFT",
        description="Coordinate system origin (TOPLEFT or BOTTOMLEFT)",
    )


class DocumentMetadata(BaseModel):
    """Top-level metadata describing an ingested document."""

    model_config = ConfigDict(frozen=True)

    doc_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename of the document")
    page_count: int = Field(..., ge=1, description="Total number of pages")
    file_size_bytes: int = Field(..., ge=0, description="Size of file in bytes")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC ingestion timestamp",
    )


class ParsedElement(BaseModel):
    """An individual layout element extracted by Docling."""

    model_config = ConfigDict(frozen=True)

    element_type: ElementType = Field(..., description="Layout classification")
    content: str = Field(..., description="Raw text or formatted Markdown table")
    page_number: int = Field(..., ge=1, description="1-indexed page number")
    section_path: str = Field(
        default="Root",
        description="Hierarchical section path (e.g. Article 8 > 8.3)",
    )
    bounding_box: BoundingBox | None = Field(
        default=None,
        description="Bounding coordinates on page",
    )


class ParsedDocument(BaseModel):
    """Container for parsed elements and document metadata."""

    model_config = ConfigDict(frozen=True)

    metadata: DocumentMetadata = Field(..., description="Document metadata")
    elements: list[ParsedElement] = Field(
        default_factory=list,
        description="Ordered sequence of extracted layout elements",
    )


class DocumentChunk(BaseModel):
    """An atomic text or table chunk with contextual breadcrumb lineage."""

    chunk_id: str = Field(
        ...,
        description="Deterministic SHA-256 identifier (doc_id + page + index)",
    )
    doc_id: str = Field(..., description="Parent document identifier")
    filename: str = Field(..., description="Parent document filename")
    page_number: int = Field(..., ge=1, description="1-indexed page number")
    chunk_index: int = Field(..., ge=0, description="0-indexed sequence in doc")
    element_type: ElementType = Field(
        default=ElementType.TEXT,
        description="Layout element classification",
    )
    section_path: str = Field(
        default="Root",
        description="Breadcrumb hierarchy (e.g., Article 8 > 8.3 Liability)",
    )
    raw_content: str = Field(
        ...,
        description="Raw text or Markdown table representation",
    )
    contextualized_content: str = Field(
        ...,
        description="Content prefixed with Document and Section breadcrumbs",
    )
    bounding_box: BoundingBox | None = Field(
        default=None,
        description="Optional page bounding box for UI highlighting",
    )

    @classmethod
    def generate_chunk_id(cls, doc_id: str, page_number: int, chunk_index: int) -> str:
        """Generate a deterministic SHA-256 chunk identifier."""
        raw_key = f"{doc_id}:{page_number}:{chunk_index}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def build_contextual_header(
        cls,
        filename: str,
        page_number: int,
        section_path: str,
        content: str,
    ) -> str:
        """Format content with standard ClauseLens breadcrumbs."""
        clean_section = section_path.strip() if section_path.strip() else "Root"
        return (
            f"[Document: {filename} | Page: {page_number}]\n"
            f"[Section: {clean_section}]\n"
            f"---\n"
            f"{content.strip()}"
        )

