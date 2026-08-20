"""Pydantic schemas for Gemini structured extraction output."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


ExtractionConfidence = Literal["high", "medium", "low"]
ExtractionSignalType = Literal[
    "friction",
    "motivation",
    "behavior",
    "uncertainty",
    "comparison",
    "external_validation",
]


class ExtractionItem(BaseModel):
    """A discrete behavioral reason, friction, or decision factor extracted from a single document."""

    reason_text: str = Field(
        ...,
        description="A concise synthesis (1 sentence) of the specific reason, behavioral friction, or decision factor mentioned.",
    )
    verbatim_quote: str = Field(
        ...,
        description="The exact substring from the source text supporting this extraction.",
    )
    confidence: ExtractionConfidence = Field(
        default="high",
        description="Confidence level in the extraction: high (explicitly stated), medium (clearly implied), low (inferred).",
    )
    signal_type: ExtractionSignalType = Field(
        default="friction",
        description="Behavioral signal classification category.",
    )
    preliminary_cluster_hint: Optional[str] = Field(
        default=None,
        description="Optional 2-4 word snake_case topic tag for clustering assistance.",
    )


class DocumentExtractionResponse(BaseModel):
    """Extraction output for a single raw document."""

    doc_id: str = Field(
        ...,
        description="The unique identifier of the source document.",
    )
    items: List[ExtractionItem] = Field(
        default_factory=list,
        description="List of discrete extractions identified in this document. Empty if non-actionable.",
    )


class BatchExtractionResponse(BaseModel):
    """Batch container for multi-document extractions."""

    documents: List[DocumentExtractionResponse] = Field(
        default_factory=list,
        description="List of document extraction results.",
    )
