"""Unit tests for multi-dimensional scoring (triangulation, segments, conversion relevance, composite)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.models.taxonomy_node import TaxonomyNode
from app.aggregation.triangulation import TriangulationScorer
from app.aggregation.segment_analyzer import SegmentAnalyzer
from app.aggregation.opportunity_scorer import OpportunityScorer


@pytest.fixture
def scoring_db():
    """In-memory SQLite test database with seeded multi-platform documents."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Create 3 documents across 3 different platforms with diverse categories
    doc1 = RawDocument(
        source_platform="reddit",
        content_text="Reddit post on kurta sizing confusion",
        content_hash="h1",
        inferred_category="ethnic_wear",
        inferred_gender_context="women",
        inferred_brand_tier="mid",
    )
    doc2 = RawDocument(
        source_platform="playstore",
        content_text="Playstore review on dress size mismatch",
        content_hash="h2",
        inferred_category="western",
        inferred_gender_context="women",
        inferred_brand_tier="premium",
    )
    doc3 = RawDocument(
        source_platform="youtube",
        content_text="YouTube comment on shoe sizing chart",
        content_hash="h3",
        inferred_category="footwear",
        inferred_gender_context="men",
        inferred_brand_tier="value",
    )
    db.add_all([doc1, doc2, doc3])
    db.flush()

    # Create Taxonomy Node
    node = TaxonomyNode(
        label="Fit & Sizing Confidence Gap",
        description="Users struggle with uncertain size charts across brands.",
        extraction_count=3,
        representative_quotes=["size chart mismatch"],
        status="auto_generated",
    )
    db.add(node)
    db.flush()

    # Link extractions
    ext1 = Extraction(doc_id=doc1.doc_id, reason_text="Sizing doubt 1", verbatim_quote="q1", signal_type="uncertainty", taxonomy_node_id=node.node_id)
    ext2 = Extraction(doc_id=doc2.doc_id, reason_text="Sizing doubt 2", verbatim_quote="q2", signal_type="uncertainty", taxonomy_node_id=node.node_id)
    ext3 = Extraction(doc_id=doc3.doc_id, reason_text="Sizing doubt 3", verbatim_quote="q3", signal_type="uncertainty", taxonomy_node_id=node.node_id)
    db.add_all([ext1, ext2, ext3])
    db.commit()

    try:
        yield db, node
    finally:
        db.close()


def test_triangulation_scoring(scoring_db):
    """Test triangulation scoring across multiple distinct platforms."""
    db, node = scoring_db
    scorer = TriangulationScorer()

    score, breakdown, confidence = scorer.compute_triangulation_for_node(db, node.node_id)

    # 3 platforms (reddit, playstore, youtube) out of 4 baseline -> 0.75
    assert score == 0.75
    assert len(breakdown) == 3
    assert "reddit" in breakdown
    assert "playstore" in breakdown
    assert "youtube" in breakdown
    assert confidence in ("high", "medium")


def test_segment_analysis(scoring_db):
    """Test segment prevalence computation and breadth entropy."""
    db, node = scoring_db
    analyzer = SegmentAnalyzer()

    breakdown, breadth_score = analyzer.analyze_segments_for_node(db, node.node_id)

    assert "by_category" in breakdown
    assert "by_gender" in breakdown
    assert "by_brand_tier" in breakdown

    # Breadth should be high because data spans ethnic_wear, western, footwear
    assert breadth_score >= 0.5
    assert 0.0 <= breadth_score <= 1.0


def test_composite_opportunity_scoring(scoring_db):
    """Test composite scoring and rank ordering."""
    db, node = scoring_db
    scorer = OpportunityScorer()

    scores = scorer.score_all_nodes(db, [node])
    assert len(scores) == 1
    s = scores[0]

    assert s.rank == 1
    assert 0.0 <= s.composite_score <= 1.0
    assert s.frequency_score == 1.0  # only 1 node, so max share
    assert s.triangulation_score == 0.75
    assert s.conversion_relevance_score > 0.5
    assert s.actionability_score > 0.5


def test_non_monetary_constraint_penalization():
    """Verify that pure price complaints are penalized in actionability score."""
    scorer = OpportunityScorer()

    # Sizing friction (highly actionable non-monetary)
    fit_rel, fit_act, _ = scorer._heuristic_business_scoring(
        "Fit & Sizing Confidence Gap", "Garment size chart discrepancies causing doubt"
    )
    assert fit_act >= 0.80

    # Pure price complaint (deprioritized per non-monetary constraint)
    price_rel, price_act, _ = scorer._heuristic_business_scoring(
        "Expensive Prices & Discounts", "Items are too pricey and users want flat discounts and sale prices"
    )
    assert price_act < 0.35
