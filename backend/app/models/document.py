from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import generate_uuid_str, get_utc_now

if TYPE_CHECKING:
    from app.models.pipeline_run import PipelineRun
    from app.models.extraction import Extraction


class RawDocument(Base):
    """Raw multi-channel feedback document ingested into the corpus."""

    __tablename__ = "raw_documents"

    doc_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid_str
    )
    source_platform: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="reddit | playstore | appstore | youtube | twitter | forum | ecommerce"
    )
    content_text: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, doc="SHA-256 hash for de-duplication"
    )
    content_language: Mapped[str] = mapped_column(
        String(10), default="en", nullable=False
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    source_subreddit: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    author_id_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, doc="Anonymized SHA-256 author ID"
    )
    engagement_score: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, doc="Upvotes, likes, or helpful ratings"
    )
    inferred_category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="ethnic_wear | western | footwear | accessories | general"
    )
    inferred_gender_context: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="women | men | unisex | unknown"
    )
    inferred_brand_tier: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="premium | mid | value | unknown"
    )
    ingestion_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("pipeline_runs.run_id", ondelete="SET NULL"), nullable=True
    )
    source_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )

    # Relationships
    ingestion_run: Mapped[Optional["PipelineRun"]] = relationship(
        "PipelineRun", back_populates="raw_documents", foreign_keys=[ingestion_run_id]
    )
    extractions: Mapped[List["Extraction"]] = relationship(
        "Extraction", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_documents_platform", "source_platform"),
        Index("idx_documents_category", "inferred_category"),
        Index("idx_documents_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        return f"<RawDocument(doc_id='{self.doc_id}', platform='{self.source_platform}', category='{self.inferred_category}')>"
