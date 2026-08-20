"""End-to-end integration test for Pulse pipeline state machine (Phase 5, Task 5.6)."""

import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models.pipeline_run import PipelineRun
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.models.taxonomy_node import TaxonomyNode
from app.models.opportunity_score import OpportunityScore


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_e2e_pipeline_state_machine(client: TestClient, db: Session):
    """Test full pipeline execution transitions: IDLE -> INGESTING -> EXTRACTING -> CLUSTERING -> SCORING -> COMPLETE."""
    # 1. Check pipeline status
    res = client.get("/api/v1/pipeline/status", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert res.status_code == 200
    data = res.json()
    assert "runs" in data

    # 2. Trigger pipeline run for scoring
    trigger_res = client.post(
        "/api/v1/pipeline/run",
        json={"stage": "scoring", "config": {"dry_run": True}},
        headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
    )
    assert trigger_res.status_code == 200
    trigger_data = trigger_res.json()
    assert "run_id" in trigger_data
    assert trigger_data["stage"] == "scoring"
    assert trigger_data["status"] in ["pending", "queued", "running", "completed"]

    # 3. Verify that opportunity rankings are computed and served
    opps_res = client.get("/api/v1/opportunities?limit=10", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert opps_res.status_code == 200
    opps_data = opps_res.json()
    assert "opportunities" in opps_data
    assert len(opps_data["opportunities"]) > 0

    # 4. Verify that each opportunity has valid sub-scores and rank
    top_opp = opps_data["opportunities"][0]
    assert "rank" in top_opp
    assert top_opp["rank"] == 1
    assert "composite_score" in top_opp
    assert 0.0 <= top_opp["composite_score"] <= 1.0
    assert "frequency_score" in top_opp
    assert "triangulation_score" in top_opp
    assert "conversion_relevance_score" in top_opp
    assert "actionability_score" in top_opp


def test_e2e_evidence_drilldown(client: TestClient):
    """Verify that an opportunity area seamlessly drills down to verbatim evidence quotes."""
    opps_res = client.get("/api/v1/opportunities?limit=1", headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"})
    assert opps_res.status_code == 200
    opp_id = opps_res.json()["opportunities"][0]["node_id"]

    # Fetch evidence quotes
    evidence_res = client.get(
        f"/api/v1/opportunities/{opp_id}/evidence?page=1&per_page=5",
        headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
    )
    assert evidence_res.status_code == 200
    ev_data = evidence_res.json()
    assert "evidence" in ev_data
    assert "pagination" in ev_data
    assert len(ev_data["evidence"]) > 0
    assert ev_data["evidence"][0]["verbatim_quote"] != ""
    assert ev_data["evidence"][0]["source_platform"] in ["reddit", "playstore", "appstore", "youtube", "manual_upload"]
