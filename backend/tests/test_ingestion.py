import os
import sys
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Base, RawDocument, PipelineRun
from app.ingestion.normalizer import normalizer, TextNormalizer
from app.ingestion.metadata_enricher import metadata_enricher, MetadataEnricher
from app.ingestion.scrapers.manual_upload import manual_upload_handler
from app.ingestion.pipeline import IngestionPipeline
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


# 1. Normalizer Tests
def test_normalizer_clean_html_and_spaces():
    raw = "<p>I wanted to buy this <b>kurta</b> on Myntra &amp; save it to wishlist!    </p>\n\n\n\nReally good."
    cleaned, content_hash = normalizer.normalize(raw)

    assert cleaned is not None
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "&amp;" not in cleaned
    assert "&" in cleaned
    assert "  " not in cleaned
    assert len(content_hash) == 64


def test_normalizer_hash_determinism():
    text1 = "I love this floral dress from Zara but not sure about sizing."
    text2 = "  I LOVE this floral   dress from Zara but not sure about sizing.  "

    _, hash1 = normalizer.normalize(text1)
    _, hash2 = normalizer.normalize(text2)

    assert hash1 == hash2


def test_normalizer_rejects_too_short():
    short_text = "Good app"
    cleaned, content_hash = normalizer.normalize(short_text)
    assert cleaned is None
    assert content_hash is None


# 2. Metadata Enricher Tests
def test_enricher_ethnic_wear():
    text = "Added this Anarkali kurta and dupatta to my wishlist for Diwali. Sizing chart seems confusing for women."
    enriched = metadata_enricher.enrich(text, initial_score=15)

    assert enriched["inferred_category"] == "ethnic_wear"
    assert enriched["inferred_gender_context"] == "women"
    assert enriched["engagement_score"] == 15


def test_enricher_western_and_premium_brand():
    text = "Looking at this Zara blazer and denim jeans for men. Sizing runs slightly tight."
    enriched = metadata_enricher.enrich(text)

    assert enriched["inferred_category"] == "western"
    assert enriched["inferred_gender_context"] == "men"
    assert enriched["inferred_brand_tier"] == "premium"


def test_enricher_footwear_and_mid_brand():
    text = "These HRX sneakers look great in cart, but not sure if UK 8 fits true to size."
    enriched = metadata_enricher.enrich(text)

    assert enriched["inferred_category"] == "footwear"
    assert enriched["inferred_brand_tier"] == "mid"


# 3. Manual Upload Parser Tests
def test_manual_upload_json():
    payload = [
        {
            "content_text": "Wishlisted this Vero Moda top 2 weeks ago. Waiting to see if fabric shrinks after wash.",
            "source_platform": "reddit",
            "source_subreddit": "r/IndianFashionAddicts",
            "engagement_score": 25,
        },
        {
            "text": "App crashes whenever I open my wishlist tab on Android.",
            "source_platform": "playstore",
            "engagement_score": 4,
        },
    ]
    docs = manual_upload_handler.parse_json(payload)
    assert len(docs) == 2
    assert docs[0].source_platform == "reddit"
    assert docs[0].source_subreddit == "r/IndianFashionAddicts"
    assert docs[0].engagement_score == 25
    assert docs[1].source_platform == "playstore"


def test_manual_upload_csv():
    csv_data = """content_text,source_platform,engagement_score
"Love this Anouk kurti but returning because length is too short for 5'4 height",ecommerce,12
"Wishlist price changed overnight without any alert on iOS app",appstore,3
"""
    docs = manual_upload_handler.parse_csv(csv_data)
    assert len(docs) == 2
    assert docs[0].source_platform == "ecommerce"
    assert docs[0].engagement_score == 12
    assert docs[1].source_platform == "appstore"


# 4. Pipeline Execution & Deduplication Tests
def test_pipeline_deduplication(test_db):
    pipeline = IngestionPipeline()

    sample_data = [
        {
            "content_text": "I added this floral Anarkali kurta to my wishlist but size M is sold out.",
            "source_platform": "reddit",
            "engagement_score": 10,
        },
        {
            # Exact duplicate text
            "content_text": "I added this floral Anarkali kurta to my wishlist but size M is sold out.",
            "source_platform": "reddit",
            "engagement_score": 5,
        },
        {
            "content_text": "Can anyone review the stitching quality on Roadster denim jackets?",
            "source_platform": "reddit",
            "engagement_score": 8,
        },
    ]

    run = pipeline.run(
        sources=["manual_upload"],
        config={"data": sample_data},
        db=test_db,
    )

    assert run.status == "completed"
    assert run.stats["total_inserted"] == 2
    assert run.stats["total_duplicates"] == 1

    stored_docs = test_db.query(RawDocument).all()
    assert len(stored_docs) == 2


# 5. Corpus & Pipeline API Routes Tests
def test_corpus_stats_and_documents_routes(client):
    # Fetch stats
    stats_res = client.get("/api/v1/corpus/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert "total_documents" in stats_data
    assert "platform_distribution" in stats_data
    assert "category_distribution" in stats_data

    # Fetch documents list
    docs_res = client.get("/api/v1/corpus/documents?page=1&per_page=10")
    assert docs_res.status_code == 200
    docs_data = docs_res.json()
    assert "pagination" in docs_data
    assert "documents" in docs_data


def test_pipeline_run_route(client):
    res = client.post(
        "/api/v1/pipeline/run",
        json={"stage": "ingestion", "sources": ["manual_upload"], "limit_per_source": 50},
    )
    assert res.status_code == 200
    data = res.json()
    assert "run_id" in data
    assert data["stage"] == "ingestion"
    assert data["status"] in ["pending", "running", "completed"]

    status_res = client.get("/api/v1/pipeline/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "runs" in status_data
    assert len(status_data["runs"]) >= 1


# 6. Edge Case Tests
def test_enricher_brand_collision_avoidance():
    # Common English sentence with "only" and "w" should NOT match brand tier mid
    common_sentence = "I only wanted to check the return policy because the width was too small."
    enriched = metadata_enricher.enrich(common_sentence)
    assert enriched["inferred_brand_tier"] == "unknown"

    # Explicit brand mention with uppercase or context SHOULD match brand tier
    brand_text_1 = "I bought this ONLY jeans from the sale."
    assert metadata_enricher.infer_brand_tier(brand_text_1) == "mid"

    brand_text_2 = "Added a dress from brand ONLY to wishlist."
    assert metadata_enricher.infer_brand_tier(brand_text_2) == "mid"

    brand_text_3 = "Saved this kurti from W for Woman in my cart."
    assert metadata_enricher.infer_brand_tier(brand_text_3) == "mid"


def test_manual_upload_csv_with_bom():
    # Simulate CSV exported from Windows Excel with UTF-8 BOM
    bom_csv = "\ufeffcontent_text,source_platform,engagement_score\n\"Great blazer from Zara with good stitching\",reddit,10\n"
    docs = manual_upload_handler.parse_csv(bom_csv)
    assert len(docs) == 1
    assert docs[0].source_platform == "reddit"
    assert "Zara" in docs[0].content_text


def test_normalizer_verbatim_quote_validation():
    source_text = "I loved this Anarkali kurta but the bust area was too tight for size M."

    # Exact match
    assert normalizer.verify_verbatim_quote("bust area was too tight", source_text) is True

    # Case & whitespace tolerant match
    assert normalizer.verify_verbatim_quote("  BUST AREA   WAS TOO TIGHT  ", source_text) is True

    # Hallucinated / altered quote
    assert normalizer.verify_verbatim_quote("the chest fitting was really tight", source_text) is False
