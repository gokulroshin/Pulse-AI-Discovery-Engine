"""REST API routes for querying structured reason extractions and auditing LLM outputs."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_db
from app.models.extraction import Extraction
from app.models.document import RawDocument

router = APIRouter(prefix="/api/v1/extractions", tags=["Reason Extractions"])


@router.get("/stats")
def get_extraction_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get aggregate statistics across all structured reason extractions."""
    total_extractions = db.query(func.count(Extraction.extraction_id)).scalar() or 0
    total_extracted_docs = (
        db.query(func.count(func.distinct(Extraction.doc_id))).scalar() or 0
    )

    signal_distribution = dict(
        db.query(Extraction.signal_type, func.count(Extraction.extraction_id))
        .group_by(Extraction.signal_type)
        .all()
    )

    confidence_distribution = dict(
        db.query(Extraction.confidence, func.count(Extraction.extraction_id))
        .group_by(Extraction.confidence)
        .all()
    )

    return {
        "total_extractions": total_extractions,
        "total_extracted_documents": total_extracted_docs,
        "signal_distribution": signal_distribution,
        "confidence_distribution": confidence_distribution,
    }


@router.get("")
def list_extractions(
    doc_id: Optional[str] = Query(None, description="Filter extractions for a specific document ID"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type (friction, motivation, uncertainty, etc.)"),
    confidence: Optional[str] = Query(None, description="Filter by confidence (high, medium, low)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """List paginated structured reason extractions with filters."""
    query = db.query(Extraction)

    if doc_id:
        query = query.filter(Extraction.doc_id == doc_id)
    if signal_type:
        query = query.filter(Extraction.signal_type == signal_type)
    if confidence:
        query = query.filter(Extraction.confidence == confidence)

    total_count = query.count()
    offset = (page - 1) * per_page
    extractions = query.order_by(Extraction.created_at.desc()).offset(offset).limit(per_page).all()

    items = []
    for ext in extractions:
        items.append({
            "extraction_id": ext.extraction_id,
            "doc_id": ext.doc_id,
            "reason_text": ext.reason_text,
            "verbatim_quote": ext.verbatim_quote,
            "confidence": ext.confidence,
            "signal_type": ext.signal_type,
            "taxonomy_node_id": ext.taxonomy_node_id,
            "extraction_run_id": ext.extraction_run_id,
            "created_at": ext.created_at.isoformat() if ext.created_at else None,
        })

    return {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": (total_count + per_page - 1) // per_page if total_count > 0 else 0,
        },
        "extractions": items,
    }


@router.get("/{extraction_id}")
def get_extraction_detail(extraction_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get deep detail of a specific extraction and its parent source document."""
    ext = db.query(Extraction).filter(Extraction.extraction_id == extraction_id).first()
    if not ext:
        raise HTTPException(status_code=404, detail="Extraction not found")

    parent_doc = db.query(RawDocument).filter(RawDocument.doc_id == ext.doc_id).first()

    return {
        "extraction": {
            "extraction_id": ext.extraction_id,
            "doc_id": ext.doc_id,
            "reason_text": ext.reason_text,
            "verbatim_quote": ext.verbatim_quote,
            "confidence": ext.confidence,
            "signal_type": ext.signal_type,
            "taxonomy_node_id": ext.taxonomy_node_id,
            "extraction_run_id": ext.extraction_run_id,
            "created_at": ext.created_at.isoformat() if ext.created_at else None,
        },
        "source_document": {
            "doc_id": parent_doc.doc_id,
            "source_platform": parent_doc.source_platform,
            "content_text": parent_doc.content_text,
            "source_url": parent_doc.source_url,
            "inferred_category": parent_doc.inferred_category,
            "inferred_gender_context": parent_doc.inferred_gender_context,
            "inferred_brand_tier": parent_doc.inferred_brand_tier,
            "engagement_score": parent_doc.engagement_score,
            "source_timestamp": parent_doc.source_timestamp.isoformat() if parent_doc.source_timestamp else None,
        } if parent_doc else None,
    }
