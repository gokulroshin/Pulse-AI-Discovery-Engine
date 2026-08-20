from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import generate_uuid_str, get_utc_now

if TYPE_CHECKING:
    from app.models.document import RawDocument
    from app.models.taxonomy_node import TaxonomyNode
    from app.models.pipeline_run import PipelineRun


class Extraction(Base):
    """Discrete qualitative reason/behavior tag extracted by Gemini from raw document."""

    __tablename__ = "extractions"

    extraction_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid_str
    )
    doc_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("raw_documents.doc_id", ondelete="CASCADE"), nullable=False
    )
    reason_text: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Concise paraphrase of specific reason/behavior"
    )
    verbatim_quote: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Exact supporting excerpt from original text"
    )
    confidence: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False, doc="high | medium | low"
    )
    signal_type: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="friction | motivation | behavior | uncertainty | comparison | external_validation"
    )
    preliminary_cluster_hint: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    taxonomy_node_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("taxonomy_nodes.node_id", ondelete="SET NULL"), nullable=True
    )
    extraction_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("pipeline_runs.run_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )

    # Relationships
    document: Mapped["RawDocument"] = relationship(
        "RawDocument", back_populates="extractions"
    )
    taxonomy_node: Mapped[Optional["TaxonomyNode"]] = relationship(
        "TaxonomyNode", back_populates="extractions"
    )
    extraction_run: Mapped[Optional["PipelineRun"]] = relationship(
        "PipelineRun", back_populates="extractions", foreign_keys=[extraction_run_id]
    )

    __table_args__ = (
        Index("idx_extractions_doc", "doc_id"),
        Index("idx_extractions_taxonomy", "taxonomy_node_id"),
        Index("idx_extractions_signal_type", "signal_type"),
    )

    def __repr__(self) -> str:
        return f"<Extraction(id='{self.extraction_id}', type='{self.signal_type}', confidence='{self.confidence}')>"
