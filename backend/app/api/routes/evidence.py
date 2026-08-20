"""Evidence drill-down REST API endpoint for sourcing raw verbatim quotes backing opportunity areas."""

import math
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.api.dependencies import verify_api_key
from app.models.taxonomy_node import TaxonomyNode
from app.models.extraction import Extraction
from app.models.document import RawDocument

router = APIRouter(prefix="/api/v1/opportunities", tags=["Evidence Explorer"])


@router.get("/{id}/evidence", summary="Get Evidence Quotes for Opportunity Area")
def get_opportunity_evidence(
    id: str,
    platform: Optional[str] = Query(None, description="Filter by source platform: reddit | playstore | appstore | youtube"),
    confidence: Optional[str] = Query(None, description="Filter by confidence: high | medium | low"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Retrieve paginated qualitative source evidence and verbatim quotes backing an opportunity area."""
    # Find taxonomy node
    node = db.query(TaxonomyNode).filter_by(node_id=id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity node '{id}' not found",
        )

    query = (
        db.query(Extraction, RawDocument)
        .join(RawDocument, Extraction.doc_id == RawDocument.doc_id)
        .filter(Extraction.taxonomy_node_id == node.node_id)
    )

    if platform:
        query = query.filter(RawDocument.source_platform == platform.lower())
    if confidence:
        query = query.filter(Extraction.confidence == confidence.lower())

    total_count = query.count()
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

    records = (
        query.order_by(desc(RawDocument.engagement_score), desc(Extraction.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    evidence_items = []
    for ext, doc in records:
        evidence_items.append({
            "extraction_id": ext.extraction_id,
            "reason_text": ext.reason_text,
            "verbatim_quote": ext.verbatim_quote,
            "signal_type": ext.signal_type,
            "confidence": ext.confidence,
            "source_platform": doc.source_platform,
            "source_url": doc.source_url,
            "source_subreddit": doc.source_subreddit,
            "engagement_score": doc.engagement_score,
            "inferred_category": doc.inferred_category,
            "inferred_gender_context": doc.inferred_gender_context,
            "inferred_brand_tier": doc.inferred_brand_tier,
            "source_timestamp": doc.source_timestamp.isoformat() if doc.source_timestamp else None,
            "extracted_at": ext.created_at.isoformat(),
        })

    return {
        "opportunity": {
            "node_id": node.node_id,
            "label": node.label,
            "description": node.description,
        },
        "evidence_count": total_count,
        "evidence": evidence_items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages,
        },
    }
