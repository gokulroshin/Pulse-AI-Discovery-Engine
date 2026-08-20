import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import (
    Base,
    RawDocument,
    TaxonomyNode,
    Extraction,
    OpportunityScore,
    PipelineRun,
)


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing ORM models and constraints."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_tables_created(test_db):
    """Verify all 5 tables are registered in Base metadata."""
    expected_tables = {
        "raw_documents",
        "extractions",
        "taxonomy_nodes",
        "opportunity_scores",
        "pipeline_runs",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_indexes_registered():
    """Verify all 10 key performance indexes from Architecture §4.2 are defined on models."""
    indexes_by_table = {
        table_name: [idx.name for idx in table.indexes]
        for table_name, table in Base.metadata.tables.items()
    }

    # Raw documents indexes
    assert "idx_documents_platform" in indexes_by_table["raw_documents"]
    assert "idx_documents_category" in indexes_by_table["raw_documents"]
    assert "idx_documents_hash" in indexes_by_table["raw_documents"]

    # Extractions indexes
    assert "idx_extractions_doc" in indexes_by_table["extractions"]
    assert "idx_extractions_taxonomy" in indexes_by_table["extractions"]
    assert "idx_extractions_signal_type" in indexes_by_table["extractions"]

    # Taxonomy nodes indexes
    assert "idx_taxonomy_parent" in indexes_by_table["taxonomy_nodes"]

    # Opportunity scores indexes
    assert "idx_scores_rank" in indexes_by_table["opportunity_scores"]
    assert "idx_scores_composite" in indexes_by_table["opportunity_scores"]

    # Pipeline runs indexes
    assert "idx_pipeline_status" in indexes_by_table["pipeline_runs"]


def test_pipeline_run_lifecycle(test_db):
    """Test creating and updating a PipelineRun."""
    run = PipelineRun(
        stage="ingestion",
        status="running",
        config={"sources": ["reddit", "playstore"]},
        stats={"target_count": 500},
    )
    test_db.add(run)
    test_db.commit()

    assert run.run_id is not None
    assert len(run.run_id) == 36
    assert run.stage == "ingestion"
    assert run.config["sources"] == ["reddit", "playstore"]

    # Update status
    run.status = "completed"
    run.stats = {**run.stats, "ingested_count": 492}
    test_db.commit()

    queried = test_db.query(PipelineRun).filter_by(run_id=run.run_id).first()
    assert queried.status == "completed"
    assert queried.stats["ingested_count"] == 492


def test_raw_document_and_extractions_flow(test_db):
    """Test creating a document, taxonomy node, extraction, and opportunity score."""
    # 1. Pipeline Run
    run = PipelineRun(stage="full_pipeline", status="running", config={}, stats={})
    test_db.add(run)
    test_db.commit()

    # 2. Raw Document
    doc = RawDocument(
        source_platform="reddit",
        source_subreddit="r/IndianFashionAddicts",
        content_text="I added this Anarkali kurta to my wishlist 3 weeks ago, but the size chart says chest is 38 while reviews say it runs small. Not sure whether to order M or L.",
        content_hash="mock_sha256_hash_12345",
        content_language="en",
        engagement_score=42,
        inferred_category="ethnic_wear",
        inferred_gender_context="women",
        inferred_brand_tier="mid",
        ingestion_run_id=run.run_id,
    )
    test_db.add(doc)
    test_db.commit()

    assert doc.doc_id is not None
    assert doc.source_platform == "reddit"

    # 3. Taxonomy Node
    node = TaxonomyNode(
        label="Fit & Sizing Confidence Gap",
        description="Shopper uncertainty regarding garment sizing consistency and body type fit.",
        extraction_count=1,
        representative_quotes=["reviews say it runs small but size chart says chest is 38"],
        status="auto_generated",
    )
    test_db.add(node)
    test_db.commit()

    assert node.node_id is not None

    # 4. Extraction
    extraction = Extraction(
        doc_id=doc.doc_id,
        reason_text="Uncertain whether M or L will fit due to discrepancy between size chart and user reviews",
        verbatim_quote="size chart says chest is 38 while reviews say it runs small. Not sure whether to order M or L",
        confidence="high",
        signal_type="uncertainty",
        preliminary_cluster_hint="fit_sizing",
        taxonomy_node_id=node.node_id,
        extraction_run_id=run.run_id,
    )
    test_db.add(extraction)
    test_db.commit()

    assert extraction.extraction_id is not None
    assert extraction.document.doc_id == doc.doc_id
    assert extraction.taxonomy_node.label == "Fit & Sizing Confidence Gap"

    # 5. Opportunity Score
    score = OpportunityScore(
        taxonomy_node_id=node.node_id,
        scoring_run_id=run.run_id,
        frequency_score=0.28,
        triangulation_score=0.83,
        conversion_relevance_score=0.92,
        segment_breadth_score=0.74,
        actionability_score=0.88,
        composite_score=0.79,
        rank=1,
        confidence_level="high",
        segment_breakdown={
            "by_category": {"ethnic_wear": 0.35, "western": 0.20},
            "by_gender": {"women": 0.32, "men": 0.18},
        },
        source_platform_breakdown={
            "reddit": 85,
            "playstore": 120,
            "youtube": 45,
        },
    )
    test_db.add(score)
    test_db.commit()

    assert score.score_id is not None
    assert score.rank == 1
    assert score.composite_score == 0.79
    assert score.taxonomy_node.label == "Fit & Sizing Confidence Gap"
