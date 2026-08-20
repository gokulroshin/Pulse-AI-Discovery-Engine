from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import generate_uuid_str, get_utc_now

if TYPE_CHECKING:
    from app.models.extraction import Extraction
    from app.models.opportunity_score import OpportunityScore


class TaxonomyNode(Base):
    """Hierarchical opportunity area node in the behavioral taxonomy."""

    __tablename__ = "taxonomy_nodes"

    node_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid_str
    )
    label: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Human-readable taxonomy cluster label"
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Detailed description of underlying behavioral pattern"
    )
    parent_node_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("taxonomy_nodes.node_id", ondelete="SET NULL"), nullable=True
    )
    extraction_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, doc="Count of mapped extractions"
    )
    representative_quotes: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False, doc="Top exemplar verbatim quotes"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="auto_generated", nullable=False, doc="auto_generated | pm_reviewed | merged | archived"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )

    # Self-referencing parent/child relationship
    parent: Mapped[Optional["TaxonomyNode"]] = relationship(
        "TaxonomyNode", remote_side=[node_id], back_populates="children"
    )
    children: Mapped[List["TaxonomyNode"]] = relationship(
        "TaxonomyNode", back_populates="parent", cascade="all, delete-orphan"
    )

    # Relationships
    extractions: Mapped[List["Extraction"]] = relationship(
        "Extraction", back_populates="taxonomy_node"
    )
    opportunity_scores: Mapped[List["OpportunityScore"]] = relationship(
        "OpportunityScore", back_populates="taxonomy_node", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_taxonomy_parent", "parent_node_id"),
    )

    def __repr__(self) -> str:
        return f"<TaxonomyNode(node_id='{self.node_id}', label='{self.label}', status='{self.status}')>"
