from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import generate_uuid_str, get_utc_now

if TYPE_CHECKING:
    from app.models.taxonomy_node import TaxonomyNode
    from app.models.pipeline_run import PipelineRun


class OpportunityScore(Base):
    """Composite and dimensional business scores computed for an opportunity area."""

    __tablename__ = "opportunity_scores"

    score_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid_str
    )
    taxonomy_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("taxonomy_nodes.node_id", ondelete="CASCADE"), nullable=False
    )
    scoring_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("pipeline_runs.run_id", ondelete="SET NULL"), nullable=True
    )
    frequency_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, doc="Prevalence across corpus (0.0 - 1.0)"
    )
    triangulation_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, doc="Cross-source platform confirmation (0.0 - 1.0)"
    )
    conversion_relevance_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, doc="LLM-assessed link to 30-day wishlist purchase (0.0 - 1.0)"
    )
    segment_breadth_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, doc="Prevalence across diverse user segments (0.0 - 1.0)"
    )
    actionability_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, doc="Feasibility via non-monetary product levers (0.0 - 1.0)"
    )
    composite_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, doc="Weighted composite opportunity rank score (0.0 - 1.0)"
    )
    rank: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Rank ordering (1 = highest priority)"
    )
    confidence_level: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False, doc="high | medium | low"
    )
    segment_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, doc="Category, gender, price tier prevalence distributions"
    )
    source_platform_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, doc="Document count by source platform"
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )

    # Relationships
    taxonomy_node: Mapped["TaxonomyNode"] = relationship(
        "TaxonomyNode", back_populates="opportunity_scores"
    )
    scoring_run: Mapped[Optional["PipelineRun"]] = relationship(
        "PipelineRun", back_populates="opportunity_scores", foreign_keys=[scoring_run_id]
    )

    __table_args__ = (
        Index("idx_scores_rank", "rank"),
        Index("idx_scores_composite", composite_score.desc()),
    )

    def __repr__(self) -> str:
        return f"<OpportunityScore(score_id='{self.score_id}', rank={self.rank}, composite={self.composite_score:.2f})>"
