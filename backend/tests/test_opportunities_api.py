"""Integration tests for Phase 3 REST API endpoints (/opportunities, /evidence, /segments, /taxonomy)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.models.taxonomy_node import TaxonomyNode
from app.models.opportunity_score import OpportunityScore


@pytest.fixture
def client_with_data():
    """FastAPI TestClient with pre-seeded database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed data
    doc = RawDocument(
        source_platform="playstore",
        content_text="Size chart is totally inaccurate for this dress",
        content_hash="api_test_doc_1",
        inferred_category="western",
        inferred_gender_context="women",
        inferred_brand_tier="mid",
        engagement_score=15,
    )
    db.add(doc)
    db.flush()

    node = TaxonomyNode(
        label="Fit & Sizing Confidence Gap",
        description="Users cannot determine their proper size due to inconsistent charts.",
        representative_quotes=["Size chart is totally inaccurate"],
        extraction_count=1,
        status="auto_generated",
    )
    db.add(node)
    db.flush()

    ext = Extraction(
        doc_id=doc.doc_id,
        reason_text="Inaccurate size chart causes fit uncertainty",
        verbatim_quote="Size chart is totally inaccurate",
        signal_type="uncertainty",
        confidence="high",
        taxonomy_node_id=node.node_id,
    )
    db.add(ext)
    db.flush()

    score = OpportunityScore(
        taxonomy_node_id=node.node_id,
        frequency_score=0.25,
        triangulation_score=0.75,
        conversion_relevance_score=0.92,
        segment_breadth_score=0.65,
        actionability_score=0.88,
        composite_score=0.79,
        rank=1,
        confidence_level="high",
        segment_breakdown={"by_category": {"western": 1.0}},
        source_platform_breakdown={"playstore": 1},
    )
    db.add(score)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)

    try:
        yield test_client, node, score
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_get_opportunities(client_with_data):
    """Test GET /api/v1/opportunities returns ranked opportunity list."""
    client, node, score = client_with_data
    response = client.get("/api/v1/opportunities")
    assert response.status_code == 200
    data = response.json()

    assert "opportunities" in data
    assert len(data["opportunities"]) == 1
    opp = data["opportunities"][0]
    assert opp["rank"] == 1
    assert opp["label"] == "Fit & Sizing Confidence Gap"
    assert opp["composite_score"] == 0.79
    assert opp["conversion_relevance_score"] == 0.92
    assert "top_sources" in opp
    assert "representative_quotes" in opp


def test_get_opportunity_detail(client_with_data):
    """Test GET /api/v1/opportunities/{id} returns single opportunity detail."""
    client, node, score = client_with_data
    response = client.get(f"/api/v1/opportunities/{node.node_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["node_id"] == node.node_id
    assert data["label"] == "Fit & Sizing Confidence Gap"
    assert data["rank"] == 1
    assert data["composite_score"] == 0.79
    assert "segment_breakdown" in data
    assert "source_platform_breakdown" in data


def test_get_opportunity_evidence(client_with_data):
    """Test GET /api/v1/opportunities/{id}/evidence returns paginated source evidence."""
    client, node, score = client_with_data
    response = client.get(f"/api/v1/opportunities/{node.node_id}/evidence")
    assert response.status_code == 200
    data = response.json()

    assert "evidence" in data
    assert data["evidence_count"] == 1
    evidence_item = data["evidence"][0]
    assert evidence_item["verbatim_quote"] == "Size chart is totally inaccurate"
    assert evidence_item["source_platform"] == "playstore"
    assert "pagination" in data
    assert data["pagination"]["total"] == 1


def test_get_segments_and_breakdown(client_with_data):
    """Test GET /api/v1/segments and GET /api/v1/segments/{dimension}/breakdown."""
    client, node, score = client_with_data

    # Dimension list
    resp1 = client.get("/api/v1/segments")
    assert resp1.status_code == 200
    dims = resp1.json()["dimensions"]
    assert len(dims) == 3
    dim_names = [d["name"] for d in dims]
    assert "category" in dim_names
    assert "gender" in dim_names

    # Breakdown by category
    resp2 = client.get("/api/v1/segments/category/breakdown")
    assert resp2.status_code == 200
    breakdown = resp2.json()["breakdown"]
    assert len(breakdown) == 1
    assert breakdown[0]["label"] == "Fit & Sizing Confidence Gap"


def test_taxonomy_crud_and_update(client_with_data):
    """Test GET /api/v1/taxonomy and PUT /api/v1/taxonomy/{id}."""
    client, node, score = client_with_data

    # Tree
    resp1 = client.get("/api/v1/taxonomy")
    assert resp1.status_code == 200
    nodes = resp1.json()["nodes"]
    assert len(nodes) == 1

    # PM Update
    resp2 = client.put(
        f"/api/v1/taxonomy/{node.node_id}",
        json={
            "label": "Fit & Body-Type Confidence Gap",
            "status": "pm_reviewed",
        },
    )
    assert resp2.status_code == 200
    updated = resp2.json()["node"]
    assert updated["label"] == "Fit & Body-Type Confidence Gap"
    assert updated["status"] == "pm_reviewed"
