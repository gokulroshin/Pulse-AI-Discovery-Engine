"""Taxonomy CRUD and PM Review REST API endpoints."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.api.dependencies import verify_api_key
from app.models.taxonomy_node import TaxonomyNode
from app.models.extraction import Extraction

router = APIRouter(prefix="/api/v1/taxonomy", tags=["Taxonomy Management"])


class TaxonomyUpdateRequest(BaseModel):
    label: Optional[str] = Field(None, description="Updated human-readable label")
    description: Optional[str] = Field(None, description="Updated behavioral description")
    status: Optional[str] = Field(None, description="Node status: auto_generated | pm_reviewed | merged | archived")
    parent_node_id: Optional[str] = Field(None, description="Parent taxonomy node ID for hierarchical nesting")
    merge_into_node_id: Optional[str] = Field(None, description="Target node ID if merging this node into another")


@router.get("", summary="Get Taxonomy Hierarchy")
def get_taxonomy_tree(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by node status"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Retrieve full opportunity taxonomy tree with node metadata and extraction counts."""
    query = db.query(TaxonomyNode)
    if status_filter:
        query = query.filter(TaxonomyNode.status == status_filter.lower())

    nodes = query.order_by(desc(TaxonomyNode.extraction_count)).all()

    return {
        "total_nodes": len(nodes),
        "nodes": [
            {
                "node_id": n.node_id,
                "label": n.label,
                "description": n.description,
                "parent_node_id": n.parent_node_id,
                "extraction_count": n.extraction_count,
                "representative_quotes": n.representative_quotes,
                "status": n.status,
                "created_at": n.created_at.isoformat(),
            }
            for n in nodes
        ],
    }


@router.put("/{id}", summary="Update Taxonomy Node (PM Review Workflow)")
def update_taxonomy_node(
    id: str,
    request: TaxonomyUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Update taxonomy node properties, status, or merge into another node."""
    node = db.query(TaxonomyNode).filter_by(node_id=id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Taxonomy node '{id}' not found",
        )

    # Handle merge operation
    if request.merge_into_node_id:
        target_node = db.query(TaxonomyNode).filter_by(node_id=request.merge_into_node_id).first()
        if not target_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merge target node '{request.merge_into_node_id}' not found",
            )
        # Re-assign extractions from this node to target
        db.query(Extraction).filter(Extraction.taxonomy_node_id == node.node_id).update(
            {Extraction.taxonomy_node_id: target_node.node_id},
            synchronize_session=False,
        )
        target_node.extraction_count += node.extraction_count
        node.status = "merged"
        node.parent_node_id = target_node.node_id
        db.commit()
        db.refresh(target_node)
        return {
            "status": "merged",
            "source_node_id": node.node_id,
            "target_node": {
                "node_id": target_node.node_id,
                "label": target_node.label,
                "extraction_count": target_node.extraction_count,
            },
        }

    # Standard update
    if request.label is not None:
        node.label = request.label.strip()
    if request.description is not None:
        node.description = request.description.strip()
    if request.status is not None:
        node.status = request.status.lower()
    if request.parent_node_id is not None:
        node.parent_node_id = request.parent_node_id

    db.commit()
    db.refresh(node)

    return {
        "status": "updated",
        "node": {
            "node_id": node.node_id,
            "label": node.label,
            "description": node.description,
            "status": node.status,
            "parent_node_id": node.parent_node_id,
            "extraction_count": node.extraction_count,
            "representative_quotes": node.representative_quotes,
        },
    }
