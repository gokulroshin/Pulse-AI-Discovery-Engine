import os
import sys
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Base, RawDocument, Extraction, PipelineRun
from app.extraction.schema import (
    ExtractionItem,
    DocumentExtractionResponse,
    BatchExtractionResponse,
)
from app.extraction.gemini_client import gemini_client
from app.extraction.batch_processor import ExtractionBatchProcessor
from app.ingestion.normalizer import normalizer
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


# 1. Prompt Isolation & Bias Guardrail Test
def test_prompt_isolation_guardrail():
    """Verify that the extraction system prompt strictly contains ZERO business/KPI keywords."""
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "extraction", "prompts", "extraction_system.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read().lower()

    forbidden_keywords = [
        "wishlist",
        "conversion",
        "30-day",
        "purchase rate",
        "myntra growth",
        "kpi",
        "revenue",
        "cart dropoff",
    ]

    for forbidden in forbidden_keywords:
        assert (
            forbidden not in prompt_text
        ), f"VIOLATION: Forbidden business keyword '{forbidden}' found in extraction system prompt!"


# 2. Pydantic Schema Validation Tests
def test_schema_valid_and_serialization():
    item = ExtractionItem(
        reason_text="Conflicting user reviews regarding shoulder fit create sizing doubt",
        verbatim_quote="reviews say it fits tight on shoulders",
        confidence="high",
        signal_type="friction",
        preliminary_cluster_hint="fit_sizing",
    )

    doc_res = DocumentExtractionResponse(doc_id="doc_123", items=[item])
    batch_res = BatchExtractionResponse(documents=[doc_res])

    json_dict = batch_res.model_dump()
    assert len(json_dict["documents"]) == 1
    assert json_dict["documents"][0]["doc_id"] == "doc_123"
    assert json_dict["documents"][0]["items"][0]["signal_type"] == "friction"


# 3. Verbatim Quote Verification Tests
def test_verbatim_quote_verification():
    source = "I love this Anouk kurta but shoulder stitching was too tight for size M."

    # Valid exact and whitespace normalized
    assert normalizer.verify_verbatim_quote("shoulder stitching was too tight", source) is True
    assert normalizer.verify_verbatim_quote("  SHOULDER STITCHING  WAS TOO TIGHT ", source) is True

    # Hallucinated / modified quote
    assert normalizer.verify_verbatim_quote("chest area was uncomfortably narrow", source) is False
    assert normalizer.verify_verbatim_quote(None, source) is False


# 4. Batch Processor & Checkpointing Unit Tests (with Mock Client)
class MockExtractionClient:
    def __init__(self):
        self.model = "mock-gemini-3.5-flash"

    def extract_batch(self, documents):
        results = []
        for doc in documents:
            text = doc["content_text"]
            items = []
            if "shoulder" in text.lower():
                items.append(
                    ExtractionItem(
                        reason_text="Shoulder fit is excessively tight",
                        verbatim_quote="shoulder stitching was too tight",
                        confidence="high",
                        signal_type="friction",
                        preliminary_cluster_hint="fit_shoulder",
                    )
                )
            if "hallucinated" in text.lower():
                items.append(
                    ExtractionItem(
                        reason_text="Imaginary reason",
                        verbatim_quote="this phrase does not exist in the source document",
                        confidence="low",
                        signal_type="friction",
                    )
                )
            results.append(DocumentExtractionResponse(doc_id=doc["doc_id"], items=items))
        return BatchExtractionResponse(documents=results)


def test_batch_processor_workflow(test_db):
    mock_client = MockExtractionClient()
    processor = ExtractionBatchProcessor(client=mock_client, batch_size=2)

    # Insert sample raw documents
    doc1 = RawDocument(
        doc_id="d1",
        source_platform="reddit",
        content_text="I love this kurta but shoulder stitching was too tight for size M.",
        content_hash="h1",
    )
    doc2 = RawDocument(
        doc_id="d2",
        source_platform="appstore",
        content_text="Good product hallucinated test case.",
        content_hash="h2",
    )
    doc3 = RawDocument(
        doc_id="d3",
        source_platform="playstore",
        content_text="Simple neutral review with no friction.",
        content_hash="h3",
    )
    test_db.add_all([doc1, doc2, doc3])
    test_db.commit()

    # Verify unextracted count
    unextracted = processor.get_unextracted_documents(test_db)
    assert len(unextracted) == 3

    # Run extraction
    run = processor.run(db=test_db)
    assert run.status == "completed"
    assert run.stats["total_documents_processed"] == 3
    assert run.stats["total_extractions"] == 1  # doc1 succeeded, doc2 hallucination rejected
    assert run.stats["total_rejected_quotes"] == 1

    # Check database persistence
    extractions = test_db.query(Extraction).all()
    assert len(extractions) == 1
    assert extractions[0].doc_id == "d1"
    assert extractions[0].signal_type == "friction"

    # Check resumption/checkpointing: subsequent call should find 2 unextracted docs (d2 and d3)
    # (Since d1 already has an extraction, d1 won't be reprocessed)
    remaining_unextracted = processor.get_unextracted_documents(test_db)
    assert len(remaining_unextracted) == 2


# 5. Extraction API Route Tests
def test_extractions_api_routes(client):
    # Test stats
    stats_res = client.get("/api/v1/extractions/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_extractions" in stats
    assert "signal_distribution" in stats

    # Test listing
    list_res = client.get("/api/v1/extractions?page=1&per_page=10")
    assert list_res.status_code == 200
    data = list_res.json()
    assert "pagination" in data
    assert "extractions" in data


# 6. Golden Set Dataset Structure Test
def test_golden_set_structure():
    golden_path = os.path.join(
        os.path.dirname(__file__), "golden_set", "golden_dataset.json"
    )
    with open(golden_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    assert len(dataset) == 20
    for entry in dataset:
        assert "doc_id" in entry
        assert "content_text" in entry
        assert "expected_signals" in entry
        assert len(entry["content_text"]) > 10
