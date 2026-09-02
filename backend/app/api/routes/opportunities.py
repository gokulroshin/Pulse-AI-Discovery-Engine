"""REST API endpoints for ranked opportunities and detail views."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.api.dependencies import verify_api_key
from app.models.opportunity_score import OpportunityScore
from app.models.taxonomy_node import TaxonomyNode
from app.models.document import RawDocument
from app.models.extraction import Extraction

router = APIRouter(prefix="/api/v1/opportunities", tags=["Opportunity Analytics"])


@router.get("", summary="Get Ranked Opportunity Areas")
def get_opportunities(
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Filter by minimum composite score"),
    confidence: Optional[str] = Query(None, description="Filter by confidence level: high | medium | low"),
    limit: int = Query(50, ge=1, le=100, description="Maximum opportunity areas to return"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Retrieve ranked opportunity areas sorted by composite score."""
    query = (
        db.query(OpportunityScore)
        .join(TaxonomyNode, OpportunityScore.taxonomy_node_id == TaxonomyNode.node_id)
        .order_by(OpportunityScore.rank.asc().nullslast(), OpportunityScore.composite_score.desc())
    )

    if min_score is not None:
        query = query.filter(OpportunityScore.composite_score >= min_score)
    if confidence:
        query = query.filter(OpportunityScore.confidence_level == confidence.lower())

    scores = query.all()
    corpus_size = db.query(RawDocument).count()
    latest_score = scores[0] if scores else None

    results = []
    seen_labels = set()
    current_rank = 1

    for s in scores:
        node = s.taxonomy_node
        if not node or not node.label:
            continue
        clean_label = node.label.strip()
        if clean_label in seen_labels:
            continue
        seen_labels.add(clean_label)

        # Extract top sources and top segments
        platform_breakdown = s.source_platform_breakdown or {}
        top_sources = sorted(platform_breakdown.keys(), key=lambda k: platform_breakdown[k], reverse=True)[:3]

        seg_breakdown = s.segment_breakdown or {}
        top_segments = []
        for dim, counts in seg_breakdown.items():
            if isinstance(counts, dict) and counts:
                top_dim_val = max(counts.keys(), key=lambda k: counts[k])
                top_segments.append(top_dim_val)

        results.append({
            "score_id": s.score_id,
            "rank": current_rank,
            "node_id": node.node_id if node else None,
            "label": clean_label,
            "description": node.description if node else "",
            "composite_score": s.composite_score,
            "frequency_score": s.frequency_score,
            "triangulation_score": s.triangulation_score,
            "conversion_relevance_score": s.conversion_relevance_score,
            "segment_breadth_score": s.segment_breadth_score,
            "actionability_score": s.actionability_score,
            "extraction_count": node.extraction_count if node else 0,
            "confidence_level": s.confidence_level,
            "top_sources": top_sources,
            "top_segments": top_segments,
            "representative_quotes": node.representative_quotes if node else [],
            "status": node.status if node else "auto_generated",
        })
        current_rank += 1
        if len(results) >= limit:
            break

    return {
        "scoring_run_id": latest_score.scoring_run_id if latest_score else None,
        "computed_at": latest_score.computed_at.isoformat() if latest_score else None,
        "corpus_size": corpus_size,
        "total_opportunities": len(results),
        "opportunities": results,
    }


@router.get("/{id}", summary="Get Single Opportunity Detail")
def get_opportunity_detail(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Retrieve in-depth score, segment breakdown, and metadata for a single opportunity area."""
    # Look up by node_id or score_id
    score = (
        db.query(OpportunityScore)
        .filter((OpportunityScore.taxonomy_node_id == id) | (OpportunityScore.score_id == id))
        .first()
    )

    if not score:
        # Check if taxonomy node exists even without score
        node = db.query(TaxonomyNode).filter_by(node_id=id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Opportunity area '{id}' not found",
            )
        return {
            "node_id": node.node_id,
            "label": node.label,
            "description": node.description,
            "extraction_count": node.extraction_count,
            "representative_quotes": node.representative_quotes,
            "status": node.status,
            "scores": None,
        }

    node = score.taxonomy_node

    return {
        "score_id": score.score_id,
        "node_id": node.node_id if node else None,
        "rank": score.rank,
        "label": node.label if node else "Unknown",
        "description": node.description if node else "",
        "composite_score": score.composite_score,
        "frequency_score": score.frequency_score,
        "triangulation_score": score.triangulation_score,
        "conversion_relevance_score": score.conversion_relevance_score,
        "segment_breadth_score": score.segment_breadth_score,
        "actionability_score": score.actionability_score,
        "confidence_level": score.confidence_level,
        "extraction_count": node.extraction_count if node else 0,
        "representative_quotes": node.representative_quotes if node else [],
        "top_sources": list((score.source_platform_breakdown or {}).keys()),
        "segment_breakdown": score.segment_breakdown,
        "source_platform_breakdown": score.source_platform_breakdown,
        "computed_at": score.computed_at.isoformat(),
        "status": node.status if node else "auto_generated",
    }
