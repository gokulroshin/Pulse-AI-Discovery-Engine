"""Segment prevalence analyzer and segment breadth quantification."""

import logging
import math
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.taxonomy_node import TaxonomyNode
from app.models.extraction import Extraction
from app.models.document import RawDocument

logger = logging.getLogger("pulse.aggregation.segment_analyzer")


class SegmentAnalyzer:
    """Computes categorical, demographic, and price-tier segment distributions and breadth scores."""

    def analyze_segments_for_node(
        self,
        db: Session,
        node_id: str,
    ) -> Tuple[Dict[str, Dict[str, float]], float]:
        """Compute segment breakdown and breadth diversity score for a taxonomy node.
        
        Returns:
            (segment_breakdown, segment_breadth_score)
        """
        # Query raw documents linked through extractions
        docs = (
            db.query(
                RawDocument.inferred_category,
                RawDocument.inferred_gender_context,
                RawDocument.inferred_brand_tier,
            )
            .join(Extraction, Extraction.doc_id == RawDocument.doc_id)
            .filter(Extraction.taxonomy_node_id == node_id)
            .all()
        )

        total_docs = len(docs)
        if total_docs == 0:
            return {
                "by_category": {},
                "by_gender": {},
                "by_brand_tier": {},
            }, 0.0

        cat_counts = {}
        gender_counts = {}
        tier_counts = {}

        for cat, gender, tier in docs:
            c = cat or "general"
            g = gender or "unknown"
            t = tier or "unknown"

            cat_counts[c] = cat_counts.get(c, 0) + 1
            gender_counts[g] = gender_counts.get(g, 0) + 1
            tier_counts[t] = tier_counts.get(t, 0) + 1

        # Normalize to proportions (0.0 - 1.0)
        by_category = {k: round(v / total_docs, 3) for k, v in cat_counts.items()}
        by_gender = {k: round(v / total_docs, 3) for k, v in gender_counts.items()}
        by_brand_tier = {k: round(v / total_docs, 3) for k, v in tier_counts.items()}

        segment_breakdown = {
            "by_category": by_category,
            "by_gender": by_gender,
            "by_brand_tier": by_brand_tier,
        }

        # Calculate segment breadth score using normalized Shannon entropy across categories & genders
        cat_entropy = self._normalized_entropy(list(by_category.values()), max_categories=5)
        gender_entropy = self._normalized_entropy(list(by_gender.values()), max_categories=3)

        # Weighted blend (60% category breadth, 40% gender breadth)
        breadth_score = round(0.6 * cat_entropy + 0.4 * gender_entropy, 3)
        # Ensure minimum base score for present data
        breadth_score = max(0.2, min(1.0, breadth_score))

        return segment_breakdown, breadth_score

    def _normalized_entropy(self, probabilities: List[float], max_categories: int) -> float:
        """Compute normalized entropy (0.0 to 1.0) of a probability distribution."""
        if not probabilities or len(probabilities) <= 1:
            return 0.2

        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)

        max_entropy = math.log2(max_categories) if max_categories > 1 else 1.0
        return min(1.0, entropy / max_entropy) if max_entropy > 0 else 0.0

    def analyze_segments_for_all(
        self,
        db: Session,
        nodes: List[TaxonomyNode],
    ) -> Dict[str, Dict[str, Any]]:
        """Batch compute segment analytics across all taxonomy nodes."""
        results = {}
        for node in nodes:
            breakdown, breadth = self.analyze_segments_for_node(db, node.node_id)
            results[node.node_id] = {
                "segment_breakdown": breakdown,
                "segment_breadth_score": breadth,
            }
        return results


# Global singleton
segment_analyzer = SegmentAnalyzer()
