"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from backend.src.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Verify health endpoint returns status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ClauseLens API"


def test_documents_stats() -> None:
    """Verify stats endpoint returns dense and sparse counts."""
    response = client.get("/api/documents/stats")
    assert response.status_code == 200
    data = response.json()
    assert "dense_count" in data
    assert "sparse_count" in data


def test_query_validation_rejects_empty_string() -> None:
    """Verify query endpoint rejects queries shorter than minimum length."""
    response = client.post("/api/query/search", json={"query": "a"})
    assert response.status_code == 422  # Pydantic validation failure

