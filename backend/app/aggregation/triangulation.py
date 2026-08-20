"""Cross-source platform triangulation scoring and confirmation metrics."""

import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.taxonomy_node import TaxonomyNode
from app.models.extraction import Extraction
from app.models.document import RawDocument

logger = logging.getLogger("pulse.aggregation.triangulation")

# Target set of independent source channels
STANDARD_PLATFORMS = {"playstore", "appstore", "reddit", "youtube", "manual_upload", "twitter", "forum"}
MIN_PLATFORMS_FOR_FULL_SCORE = 4.0


class TriangulationScorer:
    """Computes cross-source confirmation scores and platform distributions for opportunity nodes."""

    def compute_triangulation_for_node(
        self,
        db: Session,
        node_id: str,
    ) -> Tuple[float, Dict[str, int], str]:
        """Calculate triangulation metrics for a given taxonomy node.
        
        Returns:
            (triangulation_score, source_platform_breakdown, confidence_level)
        """
        # Query extractions linked to this taxonomy node and join with RawDocument
        results = (
            db.query(
                RawDocument.source_platform,
                func.count(Extraction.extraction_id),
            )
            .join(Extraction, Extraction.doc_id == RawDocument.doc_id)
            .filter(Extraction.taxonomy_node_id == node_id)
            .group_by(RawDocument.source_platform)
            .all()
        )

        breakdown = {platform: count for platform, count in results}
        distinct_platforms = len(breakdown)
        total_extractions = sum(breakdown.values())

        if total_extractions == 0:
            return 0.0, {}, "low"

        # Normalized triangulation score: 1 platform -> 0.25, 2 platforms -> 0.50, 3 platforms -> 0.75, 4+ -> 1.0
        triangulation_score = min(1.0, round(distinct_platforms / MIN_PLATFORMS_FOR_FULL_SCORE, 3))

        # Confidence level calculation (Success Criterion #3: >=2 independent sources gives high confidence)
        if distinct_platforms >= 3 or (distinct_platforms >= 2 and total_extractions >= 3):
            confidence_level = "high"
        elif distinct_platforms >= 2 or (distinct_platforms == 1 and total_extractions >= 15):
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return triangulation_score, breakdown, confidence_level

    def compute_triangulation_for_all(
        self,
        db: Session,
        nodes: List[TaxonomyNode],
    ) -> Dict[str, Dict[str, Any]]:
        """Batch compute triangulation across all taxonomy nodes."""
        results = {}
        for node in nodes:
            score, breakdown, confidence = self.compute_triangulation_for_node(db, node.node_id)
            results[node.node_id] = {
                "triangulation_score": score,
                "source_platform_breakdown": breakdown,
                "confidence_level": confidence,
                "distinct_platforms": len(breakdown),
            }
        return results


# Global singleton
triangulation_scorer = TriangulationScorer()
