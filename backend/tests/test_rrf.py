"""Unit tests for Reciprocal Rank Fusion (RRF) algorithm."""

import math
from backend.src.retrieval.rrf import RankedCandidate, compute_rrf


def test_rrf_scoring_math() -> None:
    """Verify exact 1-indexed RRF formula calculation."""
    # Chunk A is #1 in dense and #1 in sparse
    # Chunk B is #2 in dense only
    # Chunk C is #2 in sparse only
    dense_results = [("chunk_a", 0.95), ("chunk_b", 0.85)]
    sparse_results = [("chunk_a", 12.5), ("chunk_c", 10.2)]

    k = 60
    candidates = compute_rrf(dense_results, sparse_results, k=k)

    assert len(candidates) == 3

    # Candidate A: 1/(60+1) + 1/(60+1) = 2/61
    expected_score_a = (1.0 / 61.0) + (1.0 / 61.0)
    assert candidates[0].chunk_id == "chunk_a"
    assert math.isclose(candidates[0].rrf_score, expected_score_a, rel_tol=1e-6)
    assert candidates[0].dense_rank == 1
    assert candidates[0].sparse_rank == 1
    assert candidates[0].dense_score == 0.95
    assert candidates[0].sparse_score == 12.5

    # Candidate B & C: 1/(60+2) = 1/62
    expected_score_single = 1.0 / 62.0
    scores_remaining = {c.chunk_id: c.rrf_score for c in candidates[1:]}
    assert math.isclose(scores_remaining["chunk_b"], expected_score_single, rel_tol=1e-6)
    assert math.isclose(scores_remaining["chunk_c"], expected_score_single, rel_tol=1e-6)


def test_rrf_1_indexed_denominator() -> None:
    """Ensure rank denominator starts at 1 (k + 1) and never (k + 0)."""
    dense_results = [("top_item", 1.0)]
    sparse_results: list[tuple[str, float]] = []

    candidates = compute_rrf(dense_results, sparse_results, k=60)
    assert len(candidates) == 1
    # If 1-indexed: 1/(60+1) = 1/61 ~= 0.016393
    # If 0-indexed: 1/(60+0) = 1/60 ~= 0.016667
    assert math.isclose(candidates[0].rrf_score, 1.0 / 61.0, rel_tol=1e-6)
    assert candidates[0].dense_rank == 1


def test_rrf_telemetry_conversion() -> None:
    """Verify RankedCandidate converts cleanly to Pydantic RetrievalTelemetry."""
    cand = RankedCandidate(
        chunk_id="chunk_99",
        dense_rank=3,
        sparse_rank=5,
        dense_score=0.77,
        sparse_score=8.4,
        rrf_score=0.03,
    )
    telemetry = cand.to_telemetry()
    assert telemetry.chunk_id == "chunk_99"
    assert telemetry.dense_rank == 3
    assert telemetry.bm25_rank == 5
    assert telemetry.dense_score == 0.77
    assert telemetry.bm25_score == 8.4
    assert telemetry.rrf_score == 0.03
    assert telemetry.reranker_score is None

