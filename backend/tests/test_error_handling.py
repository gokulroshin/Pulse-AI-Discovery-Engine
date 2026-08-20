"""Fault injection and error handling test suite for Pulse Discovery Engine (Phase 5, Task 5.12)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.aggregation.embeddings import embedding_generator
from app.aggregation.opportunity_scorer import opportunity_scorer
from app.aggregation.taxonomy import taxonomy_manager


@pytest.fixture
def client():
    return TestClient(app)


def test_nonexistent_opportunity_404(client: TestClient):
    """Verify that querying a non-existent opportunity returns 404 with a structured error."""
    res = client.get(
        "/api/v1/opportunities/non-existent-uuid-12345",
        headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
    )
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data


def test_invalid_segment_dimension_400(client: TestClient):
    """Verify that querying an invalid segment dimension returns 400."""
    res = client.get(
        "/api/v1/segments/invalid_dimension/breakdown",
        headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
    )
    assert res.status_code == 400
    data = res.json()
    assert "detail" in data


def test_empty_insight_query_400(client: TestClient):
    """Verify that empty queries return 400 Bad Request."""
    res = client.post(
        "/api/v1/insights/ask",
        json={"question": ""},
        headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
    )
    assert res.status_code == 400


def test_embedding_offline_fallback():
    """Verify that embedding generator gracefully falls back to TF-IDF when Gemini is offline."""
    from app.aggregation.embeddings import EmbeddingGenerator
    gen = EmbeddingGenerator(api_key="")
    sample_texts = [
        "Inaccurate size chart and poor fitting dress",
        "Delivery took 8 days and refund was delayed",
        "Wishlisted item was automatically cancelled",
    ]
    vecs = gen.generate_embeddings(sample_texts)
    assert len(vecs) == len(sample_texts)
    assert len(vecs[0]) > 0


def test_taxonomy_labeling_fallback():
    """Verify that taxonomy manager generates valid labels even when LLM is offline."""
    from app.aggregation.taxonomy import TaxonomyManager
    mgr = TaxonomyManager(api_key="")
    result = mgr.label_cluster(
        exemplar_reasons=["Sizing was too small at chest", "Size chart inaccurate for kurti"],
        exemplar_quotes=["Received kurta was 2 inches smaller than stated in chart"],
        cluster_index=1,
    )
    assert "label" in result
    assert len(result["label"]) > 0
    assert "description" in result
    assert "representative_quotes" in result
