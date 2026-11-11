"""Unit tests for the contextual chunker module."""

from datetime import datetime, timezone
from backend.src.ingestion.contextual_chunker import ContextualChunker
from backend.src.schemas.document import (
    BoundingBox,
    DocumentChunk,
    DocumentMetadata,
    ElementType,
    ParsedDocument,
    ParsedElement,
)


def test_chunker_basic_text_grouping() -> None:
    """Verify elements in same section and page are grouped with breadcrumb header."""
    metadata = DocumentMetadata(
        doc_id="test_doc_001",
        filename="Contract_2024.pdf",
        page_count=1,
        file_size_bytes=1024,
        created_at=datetime.now(timezone.utc),
    )
    elements = [
        ParsedElement(
            element_type=ElementType.TEXT,
            content="This is the first sentence of the clause.",
            page_number=1,
            section_path="Article 8 > 8.1 Indemnification",
            bounding_box=BoundingBox(l=10.0, t=10.0, r=100.0, b=30.0, page_number=1),
        ),
        ParsedElement(
            element_type=ElementType.TEXT,
            content="This is the second sentence of the clause.",
            page_number=1,
            section_path="Article 8 > 8.1 Indemnification",
            bounding_box=BoundingBox(l=10.0, t=35.0, r=100.0, b=55.0, page_number=1),
        ),
    ]
    parsed_doc = ParsedDocument(metadata=metadata, elements=elements)
    chunker = ContextualChunker(max_chunk_chars=1000)

    chunks = chunker.chunk_document(parsed_doc)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.doc_id == "test_doc_001"
    assert chunk.filename == "Contract_2024.pdf"
    assert chunk.page_number == 1
    assert chunk.section_path == "Article 8 > 8.1 Indemnification"
    assert "This is the first sentence" in chunk.raw_content
    assert "This is the second sentence" in chunk.raw_content
    # Check breadcrumb header
    assert "[Document: Contract_2024.pdf | Page: 1]" in chunk.contextualized_content
    assert "[Section: Article 8 > 8.1 Indemnification]" in chunk.contextualized_content
    # Check bounding box merged
    assert chunk.bounding_box is not None
    assert chunk.bounding_box.l == 10.0
    assert chunk.bounding_box.t == 10.0
    assert chunk.bounding_box.b == 55.0


def test_chunker_section_boundary_split() -> None:
    """Verify that changing sections creates distinct chunks."""
    metadata = DocumentMetadata(
        doc_id="test_doc_002",
        filename="MSA.pdf",
        page_count=2,
        file_size_bytes=2048,
        created_at=datetime.now(timezone.utc),
    )
    elements = [
        ParsedElement(
            element_type=ElementType.TEXT,
            content="Section 1 details confidentiality rules.",
            page_number=1,
            section_path="Section 1: Confidentiality",
        ),
        ParsedElement(
            element_type=ElementType.TEXT,
            content="Section 2 details payment terms.",
            page_number=2,
            section_path="Section 2: Payment",
        ),
    ]
    parsed_doc = ParsedDocument(metadata=metadata, elements=elements)
    chunker = ContextualChunker(max_chunk_chars=1000)

    chunks = chunker.chunk_document(parsed_doc)

    assert len(chunks) == 2
    assert chunks[0].section_path == "Section 1: Confidentiality"
    assert chunks[1].section_path == "Section 2: Payment"
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2


def test_chunker_table_header_preservation() -> None:
    """Verify large tables split by row preserve markdown headers in every sub-chunk."""
    metadata = DocumentMetadata(
        doc_id="test_doc_003",
        filename="Pricing_Schedule.pdf",
        page_count=1,
        file_size_bytes=4096,
        created_at=datetime.now(timezone.utc),
    )

    # Construct table with many rows
    header = "| Tier | Service Level | Monthly Fee |\n| :--- | :--- | :--- |"
    rows = [f"| Tier {i} | SLA 99.{i}% | ${i * 500}/mo |" for i in range(1, 15)]
    table_content = f"{header}\n" + "\n".join(rows)

    element = ParsedElement(
        element_type=ElementType.TABLE,
        content=table_content,
        page_number=1,
        section_path="Schedule B > Pricing Matrix",
    )
    parsed_doc = ParsedDocument(metadata=metadata, elements=[element])

    # Max chars small enough to force split
    chunker = ContextualChunker(max_chunk_chars=200)
    chunks = chunker.chunk_document(parsed_doc)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.element_type == ElementType.TABLE
        # Header must be repeated in every chunk
        assert "| Tier | Service Level | Monthly Fee |" in chunk.raw_content
        assert "| :--- | :--- | :--- |" in chunk.raw_content
        assert "[Document: Pricing_Schedule.pdf | Page: 1]" in chunk.contextualized_content
        assert "[Section: Schedule B > Pricing Matrix]" in chunk.contextualized_content


def test_deterministic_chunk_id() -> None:
    """Verify chunk IDs are strictly deterministic given doc_id, page, and index."""
    id1 = DocumentChunk.generate_chunk_id("docA", 1, 0)
    id2 = DocumentChunk.generate_chunk_id("docA", 1, 0)
    id3 = DocumentChunk.generate_chunk_id("docA", 1, 1)

    assert id1 == id2
    assert id1 != id3

