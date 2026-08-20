from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import generate_uuid_str, get_utc_now


class PipelineRun(Base):
    """Tracks asynchronous execution runs across all pipeline stages."""

    __tablename__ = "pipeline_runs"

    run_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid_str
    )
    stage: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="ingestion | extraction | clustering | scoring | full_pipeline"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", doc="pending | running | completed | failed"
    )
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    stats: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    raw_documents: Mapped[List["RawDocument"]] = relationship(
        "RawDocument", back_populates="ingestion_run", foreign_keys="RawDocument.ingestion_run_id"
    )
    extractions: Mapped[List["Extraction"]] = relationship(
        "Extraction", back_populates="extraction_run", foreign_keys="Extraction.extraction_run_id"
    )
    opportunity_scores: Mapped[List["OpportunityScore"]] = relationship(
        "OpportunityScore", back_populates="scoring_run", foreign_keys="OpportunityScore.scoring_run_id"
    )

    __table_args__ = (
        Index("idx_pipeline_status", "stage", "status"),
    )

    def __repr__(self) -> str:
        return f"<PipelineRun(run_id='{self.run_id}', stage='{self.stage}', status='{self.status}')>"
