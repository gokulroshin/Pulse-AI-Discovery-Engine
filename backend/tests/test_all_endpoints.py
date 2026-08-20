"""Full API endpoint validation test suite for Pulse Discovery Engine (Phase 5, Task 5.7)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_endpoint_health(client: TestClient):
    """GET /health"""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "ok"]
    assert "database" in data
    assert "version" in data


def test_endpoint_corpus_stats(client: TestClient):
    """GET /api/v1/corpus/stats"""
    res = client.get("/api/v1/corpus/stats", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert res.status_code == 200
    data = res.json()
    assert "total_documents" in data
    assert "platform_distribution" in data
    assert "category_distribution" in data
    assert data["total_documents"] > 0


def test_endpoint_pipeline_status(client: TestClient):
    """GET /api/v1/pipeline/status"""
    res = client.get("/api/v1/pipeline/status", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert res.status_code == 200
    data = res.json()
    assert "runs" in data


def test_endpoint_pipeline_run(client: TestClient):
    """POST /api/v1/pipeline/run"""
    res = client.post(
        "/api/v1/pipeline/run",
        json={"stage": "clustering", "config": {}},
        headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "run_id" in data
    assert "status" in data


def test_endpoint_extractions(client: TestClient):
    """GET /api/v1/extractions"""
    res = client.get("/api/v1/extractions?page=1&per_page=10", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert res.status_code == 200
    data = res.json()
    assert "extractions" in data
    assert "pagination" in data
    assert data["pagination"]["total"] > 0


def test_endpoint_opportunities_list(client: TestClient):
    """GET /api/v1/opportunities"""
    res = client.get("/api/v1/opportunities?limit=50", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert res.status_code == 200
    data = res.json()
    assert "opportunities" in data
    assert "total_opportunities" in data
    assert data["total_opportunities"] > 0


def test_endpoint_opportunity_detail_and_evidence(client: TestClient):
    """GET /api/v1/opportunities/{id} and GET /api/v1/opportunities/{id}/evidence"""
    # 1. Grab first opportunity ID
    opps = client.get("/api/v1/opportunities?limit=1", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"}).json()
    opp_id = opps["opportunities"][0]["node_id"]

    # 2. Detail
    detail_res = client.get(f"/api/v1/opportunities/{opp_id}", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["node_id"] == opp_id
    assert "composite_score" in detail_data
    assert "conversion_relevance_score" in detail_data

    # 3. Evidence
    ev_res = client.get(f"/api/v1/opportunities/{opp_id}/evidence", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert "evidence" in ev_data


def test_endpoint_segments_and_breakdown(client: TestClient):
    """GET /api/v1/segments and GET /api/v1/segments/{dim}/breakdown"""
    # 1. Dimensions list
    dims_res = client.get("/api/v1/segments", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert dims_res.status_code == 200
    dims_data = dims_res.json()
    assert "dimensions" in dims_data
    assert len(dims_data["dimensions"]) >= 3

    # 2. Breakdown for category
    breakdown_res = client.get("/api/v1/segments/category/breakdown", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert breakdown_res.status_code == 200
    breakdown_data = breakdown_res.json()
    assert "breakdown" in breakdown_data
    assert "dimension" in breakdown_data


def test_endpoint_taxonomy(client: TestClient):
    """GET /api/v1/taxonomy"""
    tax_res = client.get("/api/v1/taxonomy", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert tax_res.status_code == 200
    tax_data = tax_res.json()
    assert "nodes" in tax_data
    assert "total_nodes" in tax_data


def test_endpoint_ai_insights(client: TestClient):
    """POST /api/v1/insights/ask"""
    from unittest.mock import patch
    mock_res = {
        "summary": "Postponement is driven by lack of styling context and sale anticipation.",
        "detailed_synthesis": "Users evaluate multiple factors before purchasing.",
        "key_drivers": ["Event Date Buffer", "Incomplete Outfit Context"],
        "segment_nuances": {"ethnic_wear": "Higher dependency on fabric transparency"}
    }
    with patch("app.api.routes.insights.call_gemini_rag_synthesis", return_value=mock_res):
        ins_res = client.post(
            "/api/v1/insights/ask",
            json={"question": "What causes users to postpone fashion purchases?"},
            headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
        )
        assert ins_res.status_code == 200
        ins_data = ins_res.json()
        assert "summary" in ins_data
        assert "key_drivers" in ins_data
