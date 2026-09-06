"""Segment analysis REST API endpoints."""

import time
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

# In-memory cache for ultra-fast response times
_SEGMENT_CACHE: Dict[str, Any] = {}
_CACHE_TIMESTAMP: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0


def _is_cache_valid() -> bool:
    return (time.time() - _CACHE_TIMESTAMP) < _CACHE_TTL_SECONDS


@router.get("", summary="Get Available Segment Dimensions and Values")
def get_segment_dimensions(
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """List all available segment dimensions and distinct values currently in the corpus."""
    cache_key = "dimensions"
    if _is_cache_valid() and cache_key in _SEGMENT_CACHE:
        return _SEGMENT_CACHE[cache_key]

    categories = [
        r[0] for r in db.query(RawDocument.inferred_category).distinct().filter(RawDocument.inferred_category.isnot(None)).all()
    ]
    genders = [
        r[0] for r in db.query(RawDocument.inferred_gender_context).distinct().filter(RawDocument.inferred_gender_context.isnot(None)).all()
    ]
    tiers = [
        r[0] for r in db.query(RawDocument.inferred_brand_tier).distinct().filter(RawDocument.inferred_brand_tier.isnot(None)).all()
    ]

    res = {
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
    _SEGMENT_CACHE[cache_key] = res
    return res


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

    norm_dim = dimension.lower().strip()
    key = dim_key_map.get(norm_dim)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid segment dimension '{dimension}'. Choose from: category, gender, brand_tier",
        )

    cache_key = f"breakdown_{norm_dim}"
    if _is_cache_valid() and cache_key in _SEGMENT_CACHE:
        return _SEGMENT_CACHE[cache_key]

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

    res = {
        "dimension": norm_dim,
        "total_opportunities": len(breakdown_list),
        "breakdown": breakdown_list,
    }
    _SEGMENT_CACHE[cache_key] = res
    return res
