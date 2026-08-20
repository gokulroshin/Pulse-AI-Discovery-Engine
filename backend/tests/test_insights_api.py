"""Integration tests for AI Insight Search endpoint (Phase 5, Task 5.7)."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_ask_ai_insight_core_questions(client: TestClient):
    """Test that core consumer discovery questions and custom questions receive grounded responses."""
    test_questions = [
        "Why do users add fashion products to their wishlist?",
        "What prevents wishlisted products from eventually being purchased?",
        "What uncertainties remain after users have identified a product they like?",
        "What do customers say about courier delivery delays and tracking?",
    ]

    mock_rag_response = {
        "summary": "Customers express deep frustration with courier delivery and tracking, highlighting deceptive practices.",
        "detailed_synthesis": "Analysis shows that users actively evaluate product features and sizing. When delivery delays arise, consumers postpone further checkout.",
        "key_drivers": [
            "Delivery agents making brief missed calls to falsely mark customers as unreachable",
            "Automated emails claiming failed contact attempts despite no actual calls being placed",
            "Inaccurate tracking systems displaying attempted statuses"
        ],
        "segment_nuances": {
            "ethnic_wear": "Higher dependency on fabric transparency reviews and drape verification.",
            "western_wear": "Fast-paced trend evaluation with high sensitivity to stretch and fit measurements."
        }
    }

    with patch("app.api.routes.insights.call_gemini_rag_synthesis", return_value=mock_rag_response):
        for q in test_questions:
            res = client.post(
                "/api/v1/insights/ask",
                json={"question": q},
                headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
            )
            assert res.status_code == 200, f"Failed for question: {q}"
            data = res.json()

            # Check required fields
            assert data["question"] == q
            assert len(data["summary"]) > 20
            assert len(data["detailed_synthesis"]) > 50
            assert len(data["key_drivers"]) >= 3
            assert len(data["supporting_evidence"]) >= 3
            assert len(data["linked_opportunities"]) >= 1

            # Check evidence item shape
            first_quote = data["supporting_evidence"][0]
            assert "verbatim_quote" in first_quote
            assert "source_platform" in first_quote
            assert "reason_text" in first_quote


def test_ask_ai_insight_with_filters(client: TestClient):
    """Test AI insight query with category and platform filters."""
    mock_rag_response = {
        "summary": "Sizing uncertainty in ethnic wear is driven by non-standard brand measurements.",
        "detailed_synthesis": "Consumers face challenges predicting fit in traditional silhouettes.",
        "key_drivers": ["Brand size chart variations", "Chest to hip proportion mismatches"],
        "segment_nuances": {"ethnic_wear": "Higher return rates on unstitched and semi-stitched sets"}
    }
    with patch("app.api.routes.insights.call_gemini_rag_synthesis", return_value=mock_rag_response):
        res = client.post(
            "/api/v1/insights/ask",
            json={
                "question": "Why is sizing uncertainty high in ethnic wear?",
                "category": "ethnic_wear",
                "platform": "reddit",
            },
            headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["summary"]) > 10
        assert len(data["supporting_evidence"]) > 0


def test_ask_ai_insight_empty_validation(client: TestClient):
    """Test that empty query strings are rejected with 400 Bad Request."""
    res = client.post(
        "/api/v1/insights/ask",
        json={"question": "   "},
        headers={"X-API-Key": "pulse-secret-dev-key-change-in-prod"},
    )
    assert res.status_code == 400
