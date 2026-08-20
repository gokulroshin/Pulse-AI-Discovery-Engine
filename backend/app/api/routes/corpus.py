import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.session import get_db
from app.api.dependencies import verify_api_key
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.models.pipeline_run import PipelineRun
from app.ingestion.scrapers.manual_upload import manual_upload_handler
from app.ingestion.pipeline import pipeline

router = APIRouter(prefix="/api/v1/corpus", tags=["Corpus Management"])


@router.get("/stats", summary="Get Corpus Statistics")
def get_corpus_stats(
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Returns aggregated corpus metrics across sources, categories, and gender contexts."""
    total_docs = db.query(func.count(RawDocument.doc_id)).scalar() or 0
    total_extractions = db.query(func.count(Extraction.extraction_id)).scalar() or 0

    # Platform distribution
    platform_rows = (
        db.query(RawDocument.source_platform, func.count(RawDocument.doc_id))
        .group_by(RawDocument.source_platform)
        .all()
    )
    platform_distribution = {row[0]: row[1] for row in platform_rows}

    # Category distribution
    category_rows = (
        db.query(RawDocument.inferred_category, func.count(RawDocument.doc_id))
        .group_by(RawDocument.inferred_category)
        .all()
    )
    category_distribution = {row[0]: row[1] for row in category_rows if row[0]}

    # Gender distribution
    gender_rows = (
        db.query(RawDocument.inferred_gender_context, func.count(RawDocument.doc_id))
        .group_by(RawDocument.inferred_gender_context)
        .all()
    )
    gender_distribution = {row[0]: row[1] for row in gender_rows if row[0]}

    # Brand tier distribution
    brand_rows = (
        db.query(RawDocument.inferred_brand_tier, func.count(RawDocument.doc_id))
        .group_by(RawDocument.inferred_brand_tier)
        .all()
    )
    brand_tier_distribution = {row[0]: row[1] for row in brand_rows if row[0]}

    # Last ingestion run timestamp
    last_run = (
        db.query(PipelineRun)
        .filter(PipelineRun.stage == "ingestion", PipelineRun.status == "completed")
        .order_by(desc(PipelineRun.completed_at))
        .first()
    )

    return {
        "total_documents": total_docs,
        "total_extractions": total_extractions,
        "platform_distribution": platform_distribution,
        "category_distribution": category_distribution,
        "gender_distribution": gender_distribution,
        "brand_tier_distribution": brand_tier_distribution,
        "last_ingestion_at": last_run.completed_at.isoformat() if last_run and last_run.completed_at else None,
    }


@router.get("/documents", summary="List Ingested Documents")
def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    platform: Optional[str] = Query(None, description="Filter by source platform"),
    category: Optional[str] = Query(None, description="Filter by inferred category"),
    gender: Optional[str] = Query(None, description="Filter by gender context"),
    search: Optional[str] = Query(None, description="Search text within document content"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Returns paginated raw documents with optional filtering and search."""
    query = db.query(RawDocument)

    if platform:
        query = query.filter(RawDocument.source_platform == platform.lower())
    if category:
        query = query.filter(RawDocument.inferred_category == category.lower())
    if gender:
        query = query.filter(RawDocument.inferred_gender_context == gender.lower())
    if search:
        query = query.filter(RawDocument.content_text.ilike(f"%{search}%"))

    total = query.count()
    offset = (page - 1) * per_page
    documents = (
        query.order_by(desc(RawDocument.created_at))
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
        "documents": [
            {
                "doc_id": d.doc_id,
                "source_platform": d.source_platform,
                "content_text": d.content_text,
                "content_language": d.content_language,
                "source_url": d.source_url,
                "source_subreddit": d.source_subreddit,
                "engagement_score": d.engagement_score,
                "inferred_category": d.inferred_category,
                "inferred_gender_context": d.inferred_gender_context,
                "inferred_brand_tier": d.inferred_brand_tier,
                "source_timestamp": d.source_timestamp.isoformat() if d.source_timestamp else None,
                "created_at": d.created_at.isoformat(),
            }
            for d in documents
        ],
    }


@router.post("/upload", summary="Upload Corpus CSV/JSON")
async def upload_corpus(
    file: Optional[UploadFile] = File(None),
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Upload CSV or JSON file containing curated qualitative feedback to ingest into the corpus."""
    raw_docs = []

    if file:
        content = await file.read()
        filename = file.filename or ""
        if filename.endswith(".csv"):
            raw_docs = manual_upload_handler.parse_csv(content)
        elif filename.endswith(".json"):
            raw_docs = manual_upload_handler.parse_json(content)
        else:
            # Attempt JSON first, then CSV
            try:
                raw_docs = manual_upload_handler.parse_json(content)
            except Exception:
                raw_docs = manual_upload_handler.parse_csv(content)
    elif payload:
        raw_docs = manual_upload_handler.parse_json(payload)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either a multipart file upload (CSV/JSON) or JSON request body.",
        )

    if not raw_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid text documents could be parsed from the provided input.",
        )

    # Process and store via pipeline
    result = pipeline.run(
        sources=["manual_upload"],
        config={"data": [d.__dict__ for d in raw_docs]},
        db=db
    )

    return {
        "message": "Corpus upload processed successfully",
        "run_id": result.run_id,
        "stats": result.stats,
    }
