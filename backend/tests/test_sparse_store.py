"""Unit tests for the BM25 sparse keyword store and legal tokenizer."""

import tempfile
from pathlib import Path
from backend.src.indexing.sparse_store import SparseBM25Store, legal_tokenizer
from backend.src.schemas.document import DocumentChunk, ElementType


def test_legal_tokenizer_preserves_identifiers() -> None:
    """Ensure legal numbers, currencies, percentages, and hyphenated terms are intact."""
    sample_text = (
        "Under Section 11.4(b), the vendor must maintain SOC-2 Type II certification. "
        "The liability cap shall not exceed $1,500,000 or 15% of total fees. "
        "The system uptime must be at least 99.9%."
    )
    tokens = legal_tokenizer(sample_text)

    # Identifiers must be present in token list (normalized lowercase)
    assert "11.4(b)" in tokens
    assert "soc-2" in tokens
    assert "$1,500,000" in tokens
    assert "15%" in tokens
    assert "99.9%" in tokens

    # Stopwords like 'the', 'must', 'of' (in ENGLISH_STOPWORDS) should be filtered
    assert "the" not in tokens
    assert "of" not in tokens


def test_sparse_bm25_store_search_and_persistence() -> None:
    """Verify BM25 indexing, searching, and atomic disk persistence."""
    store = SparseBM25Store()

    chunk1 = DocumentChunk(
        chunk_id="chunk_001",
        doc_id="doc_a",
        filename="Security_Addendum.pdf",
        page_number=3,
        chunk_index=0,
        element_type=ElementType.TEXT,
        section_path="Section 4 > Compliance",
        raw_content="Vendor must provide annual SOC-2 audit reports.",
        contextualized_content="[Document: Security_Addendum.pdf | Page: 3]\n[Section: Section 4 > Compliance]\n---\nVendor must provide annual SOC-2 audit reports.",
    )

    chunk2 = DocumentChunk(
        chunk_id="chunk_002",
        doc_id="doc_b",
        filename="Pricing.pdf",
        page_number=1,
        chunk_index=0,
        element_type=ElementType.TEXT,
        section_path="Pricing",
        raw_content="Annual platform fee is $50,000 payable net 30.",
        contextualized_content="[Document: Pricing.pdf | Page: 1]\n[Section: Pricing]\n---\nAnnual platform fee is $50,000 payable net 30.",
    )

    store.add_chunks([chunk1, chunk2])
    assert store.total_chunks == 2

    # Search for SOC-2
    results = store.search("SOC-2 compliance", top_k=5)
    assert len(results) > 0
    top_chunk_id, score = results[0]
    assert top_chunk_id == "chunk_001"
    assert score > 0.0

    # Search with doc_id filter
    filtered_results = store.search("annual fee", top_k=5, doc_ids=["doc_a"])
    # doc_a has "annual" but not "$50,000"
    for cid, _ in filtered_results:
        assert cid == "chunk_001"

    # Test disk persistence in a temp directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = Path(tmp_dir)
        store.save(save_path)

        # Load into new store instance
        loaded_store = SparseBM25Store()
        loaded_store.load(save_path)

        assert loaded_store.total_chunks == 2
        loaded_results = loaded_store.search("SOC-2 audit", top_k=5)
        assert len(loaded_results) > 0
        assert loaded_results[0][0] == "chunk_001"

