"""Unit tests for the grounded generator and citation hydration."""

from backend.src.generation.generator import GroundedGenerator
from backend.src.generation.prompts import format_context_block
from backend.src.schemas.document import BoundingBox
from backend.src.schemas.query import RetrievalTelemetry, ScoredChunk


def test_format_context_block() -> None:
    """Verify context block format preserves chunk ID, page, and breadcrumbs."""
    chunks = [
        {
            "chunk_id": "chunk_abc123",
            "filename": "MSA_2024.pdf",
            "page_number": 4,
            "section_path": "Article 11 > 11.4 Liability",
            "contextualized_content": "Limitation of liability capped at $1,000,000.",
        }
    ]
    block = format_context_block(chunks)
    assert "chunk_abc123" in block
    assert "MSA_2024.pdf" in block
    assert "Page: 4" in block
    assert "Article 11 > 11.4 Liability" in block
    assert "Limitation of liability capped at $1,000,000." in block


def test_grounded_generator_citations_and_bounding_box_hydration() -> None:
    """Verify generator maps citations back to exact chunk metadata and bounding box."""
    bbox = BoundingBox(l=15.0, t=25.0, r=200.0, b=45.0, page_number=2)
    telemetry = RetrievalTelemetry(
        chunk_id="chunk_test_1",
        dense_rank=1,
        bm25_rank=1,
        dense_score=0.92,
        bm25_score=14.5,
        rrf_score=0.032,
        reranker_score=0.88,
    )
    chunk = ScoredChunk(
        chunk_id="chunk_test_1",
        doc_id="doc_xyz",
        filename="Vendor_Agreement.pdf",
        page_number=2,
        section_path="Section 5 > Termination",
        raw_content="Either party may terminate upon 30 days written notice.",
        contextualized_content="[Document: Vendor_Agreement.pdf | Page: 2]\n[Section: Section 5 > Termination]\n---\nEither party may terminate upon 30 days written notice.",
        bounding_box=bbox,
        telemetry=telemetry,
    )

    generator = GroundedGenerator()
    response = generator.generate(
        query="What is the termination notice period?",
        retrieved_chunks=[chunk],
    )

    assert response.query == "What is the termination notice period?"
    assert "[1]" in response.answer
    assert len(response.citations) > 0

    citation = response.citations[0]
    assert citation.citation_id == 1
    assert citation.chunk_id == "chunk_test_1"
    assert citation.doc_name == "Vendor_Agreement.pdf"
    assert citation.page_number == 2
    assert citation.section_path == "Section 5 > Termination"
    assert citation.bounding_box is not None
    assert citation.bounding_box.l == 15.0
    assert citation.bounding_box.b == 45.0

    # Ensure telemetry is passed through
    assert len(response.telemetry) == 1
    assert response.telemetry[0].reranker_score == 0.88
    assert response.total_latency_ms >= 0.0

