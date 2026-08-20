"""Segment analysis REST API endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db.session import get_db
from app.api.dependencies import verify_api_key
from app.models.document import RawDocument
from app.models.opportunity_score import OpportunityScore
from app.models.taxonomy_node import TaxonomyNode

router = APIRouter(prefix="/api/v1/segments", tags=["Segment Analytics"])


@router.get("", summary="Get Available Segment Dimensions and Values")
def get_segment_dimensions(
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """List all available segment dimensions and distinct values currently in the corpus."""
    categories = [
        r[0] for r in db.query(RawDocument.inferred_category).distinct().filter(RawDocument.inferred_category.isnot(None)).all()
    ]
    genders = [
        r[0] for r in db.query(RawDocument.inferred_gender_context).distinct().filter(RawDocument.inferred_gender_context.isnot(None)).all()
    ]
    tiers = [
        r[0] for r in db.query(RawDocument.inferred_brand_tier).distinct().filter(RawDocument.inferred_brand_tier.isnot(None)).all()
    ]

    return {
        "dimensions": [
            {
                "name": "category",
                "label": "Product Category",
                "values": sorted(categories),
            },
            {
                "name": "gender",
                "label": "Gender Context",
                "values": sorted(genders),
            },
            {
                "name": "brand_tier",
                "label": "Brand Price Tier",
                "values": sorted(tiers),
            },
        ]
    }


@router.get("/{dimension}/breakdown", summary="Get Opportunity Breakdown by Segment Dimension")
def get_segment_breakdown(
    dimension: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Retrieve opportunity area distribution for a given segment dimension (category | gender | brand_tier)."""
    dim_key_map = {
        "category": "by_category",
        "gender": "by_gender",
        "brand_tier": "by_brand_tier",
        "price_tier": "by_brand_tier",
    }

    key = dim_key_map.get(dimension.lower())
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid segment dimension '{dimension}'. Choose from: category, gender, brand_tier",
        )

    scores = (
        db.query(OpportunityScore)
        .join(TaxonomyNode, OpportunityScore.taxonomy_node_id == TaxonomyNode.node_id)
        .order_by(OpportunityScore.rank.asc())
        .all()
    )

    breakdown_list = []
    for s in scores:
        node = s.taxonomy_node
        node_segments = (s.segment_breakdown or {}).get(key, {})

        breakdown_list.append({
            "node_id": node.node_id if node else None,
            "label": node.label if node else "Unknown",
            "rank": s.rank,
            "composite_score": s.composite_score,
            "segment_distribution": node_segments,
        })

    return {
        "dimension": dimension.lower(),
        "breakdown": breakdown_list,
    }
