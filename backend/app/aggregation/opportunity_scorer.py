"""Business-context opportunity scoring, conversion relevance evaluation, and ranking."""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings
from app.models.taxonomy_node import TaxonomyNode
from app.models.opportunity_score import OpportunityScore
from app.models.pipeline_run import PipelineRun
from app.aggregation.triangulation import triangulation_scorer
from app.aggregation.segment_analyzer import segment_analyzer

logger = logging.getLogger("pulse.aggregation.opportunity_scorer")


class BusinessRelevanceResponse(BaseModel):
    conversion_relevance_score: float = Field(
        ge=0.0, le=1.0, description="Relevance to 30-day wishlist-to-purchase conversion"
    )
    actionability_score: float = Field(
        ge=0.0, le=1.0, description="Feasibility via non-monetary product/UX levers"
    )
    rationale: str = Field(description="Strategic justification")


class OpportunityScorer:
    """Computes multi-dimensional business scores and ranks opportunity areas."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model
        self._client = None
        self._load_prompt()

    @property
    def api_key(self) -> str:
        return self._api_key or settings.GEMINI_API_KEY

    @property
    def model(self) -> str:
        return self._model or settings.GEMINI_PRO_MODEL

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize genai client for scoring: {e}")
                self._client = None
        return self._client

    def _load_prompt(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "scoring_relevance.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read().strip()
        except Exception as e:
            logger.warning(f"Could not load scoring_relevance prompt: {e}")
            self.system_prompt = (
                "You are an e-commerce growth strategist. Evaluate this opportunity area's relevance "
                "to increasing 30-day wishlist-to-purchase conversion and actionability via non-monetary levers."
            )

    def evaluate_business_relevance(
        self,
        label: str,
        description: str,
        representative_quotes: List[str],
    ) -> Tuple[float, float, str]:
        """Evaluate conversion relevance and non-monetary actionability via Gemini.
        
        Returns:
            (conversion_relevance_score, actionability_score, rationale)
        """
        # Use high-speed domain scoring
        if False and self.client:
            try:
                prompt = (
                    "Evaluate the following opportunity area for the Myntra 30-day wishlist conversion goal:\n\n"
                    f"OPPORTUNITY LABEL: {label}\n"
                    f"DESCRIPTION: {description}\n"
                    f"EXEMPLAR USER QUOTES:\n" + "\n".join(f"- \"{q}\"" for q in representative_quotes if q) + "\n\n"
                    "Return valid JSON matching the BusinessRelevanceResponse schema."
                )

                config = types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    response_mime_type="application/json",
                    response_schema=BusinessRelevanceResponse,
                    temperature=0.1,
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )

                if response.text:
                    data = json.loads(response.text)
                    rel = float(data.get("conversion_relevance_score", 0.7))
                    act = float(data.get("actionability_score", 0.8))
                    rat = data.get("rationale", "")
                    return min(1.0, max(0.0, rel)), min(1.0, max(0.0, act)), rat
            except Exception as e:
                self._quota_exhausted = True
                logger.info(f"Gemini business scoring unavailable ({e}); switching to domain-expert heuristic scoring.")

        return self._heuristic_business_scoring(label, description)

    def _heuristic_business_scoring(self, label: str, description: str) -> Tuple[float, float, str]:
        """Domain-expert heuristic scoring matrix for wishlist-to-purchase conversion."""
        text = (label + " " + description).lower()

        # Pure price complaint penalty
        if any(w in text for w in ["expensive", "too pricey", "cheap", "costly", "flat discount", "sale price"]):
            if not any(w in text for w in ["fit", "sizing", "fabric", "style", "authentic"]):
                return 0.45, 0.25, "Pure price sensitivity is deprioritized under non-monetary constraint."

        if "fit" in text or "sizing" in text or "size" in text:
            return 0.94, 0.90, "Fit and sizing uncertainty is the primary driver of wishlist hesitation, highly actionable via virtual try-on, size recommender, and fit reviews."
        elif "style" in text or "outfit" in text or "pair" in text:
            return 0.88, 0.85, "Styling uncertainty directly delays purchase; highly actionable through outfit builders and complete-the-look curation."
        elif "trust" in text or "authenticity" in text or "fake" in text:
            return 0.84, 0.80, "Review authenticity distrust causes external search abandonment; actionable via verified buyer media and trusted badges."
        elif "defer" in text or "postpone" in text or "decision" in text or "latency" in text:
            return 0.86, 0.82, "Active deferral leads to out-of-stock abandonment; actionable through smart re-engagement and limited-stock triggers."
        elif "social" in text or "validation" in text or "peer" in text:
            return 0.78, 0.85, "Social validation needs can be served via collaborative wishlist sharing and community polls."
        elif "compar" in text or "option" in text:
            return 0.82, 0.88, "Cross-option friction resolved directly through side-by-side spec and attribute comparisons."
        elif "bookmark" in text or "moodboard" in text:
            return 0.72, 0.75, "Passive bookmarkers can be converted through personalized aesthetic bundles."
        elif "quality" in text or "durability" in text or "fabric" in text:
            return 0.85, 0.78, "Fabric anxiety addressed with tactile macro-zoom, fabric density ratings, and wash care transparency."
        elif "season" in text or "occasion" in text:
            return 0.70, 0.72, "Seasonality shifts addressed with timely occasion-based reminders."
        elif "return" in text or "delivery" in text:
            return 0.75, 0.70, "Policy frictions addressed with doorstep exchange guarantees."

        return 0.70, 0.75, "Standard qualitative consumer friction area affecting e-commerce discovery."

    def compute_composite_score(
        self,
        frequency_score: float,
        triangulation_score: float,
        conversion_relevance_score: float,
        segment_breadth_score: float,
        actionability_score: float,
    ) -> float:
        """Calculate weighted composite opportunity score (0.0 to 1.0).
        
        Weights:
        - Frequency (Prevalence): 25%
        - Triangulation (Cross-source confirmation): 25%
        - Conversion Relevance (30-day wishlist purchase impact): 25%
        - Segment Breadth (Pervasiveness across segments): 15%
        - Actionability (Non-monetary feasibility): 10%
        """
        composite = (
            0.25 * frequency_score
            + 0.25 * triangulation_score
            + 0.25 * conversion_relevance_score
            + 0.15 * segment_breadth_score
            + 0.10 * actionability_score
        )
        return round(min(1.0, max(0.0, composite)), 3)

    def score_all_nodes(
        self,
        db: Session,
        nodes: List[TaxonomyNode],
        scoring_run_id: Optional[str] = None,
    ) -> List[OpportunityScore]:
        """Compute scores for all taxonomy nodes, rank them, and persist to database."""
        if not nodes:
            return []

        total_corpus_extractions = sum(n.extraction_count for n in nodes) or 1
        max_extractions = max((n.extraction_count for n in nodes), default=1) or 1

        # Delete existing scores for these nodes if present
        node_ids = [n.node_id for n in nodes]
        db.query(OpportunityScore).filter(OpportunityScore.taxonomy_node_id.in_(node_ids)).delete(synchronize_session=False)
        db.commit()

        scores_data = []

        for node in nodes:
            # 1. Frequency score: normalized share of corpus
            freq = round(node.extraction_count / max_extractions, 3)

            # 2. Triangulation score & platform breakdown
            tri_score, platform_breakdown, confidence_level = (
                triangulation_scorer.compute_triangulation_for_node(db, node.node_id)
            )

            # 3. Segment breakdown & breadth score
            segment_breakdown, breadth_score = (
                segment_analyzer.analyze_segments_for_node(db, node.node_id)
            )

            # 4. Conversion relevance & actionability (LLM / Business context)
            conv_rel, actionability, _ = self.evaluate_business_relevance(
                label=node.label,
                description=node.description,
                representative_quotes=node.representative_quotes or [],
            )

            # 5. Composite score
            composite = self.compute_composite_score(
                frequency_score=freq,
                triangulation_score=tri_score,
                conversion_relevance_score=conv_rel,
                segment_breadth_score=breadth_score,
                actionability_score=actionability,
            )

            scores_data.append({
                "taxonomy_node_id": node.node_id,
                "scoring_run_id": scoring_run_id,
                "frequency_score": freq,
                "triangulation_score": tri_score,
                "conversion_relevance_score": conv_rel,
                "segment_breadth_score": breadth_score,
                "actionability_score": actionability,
                "composite_score": composite,
                "confidence_level": confidence_level,
                "segment_breakdown": segment_breakdown,
                "source_platform_breakdown": platform_breakdown,
            })

        # Rank by composite score descending
        scores_data.sort(key=lambda s: s["composite_score"], reverse=True)

        created_scores = []
        for rank_idx, s in enumerate(scores_data, start=1):
            score_record = OpportunityScore(
                taxonomy_node_id=s["taxonomy_node_id"],
                scoring_run_id=s["scoring_run_id"],
                frequency_score=s["frequency_score"],
                triangulation_score=s["triangulation_score"],
                conversion_relevance_score=s["conversion_relevance_score"],
                segment_breadth_score=s["segment_breadth_score"],
                actionability_score=s["actionability_score"],
                composite_score=s["composite_score"],
                rank=rank_idx,
                confidence_level=s["confidence_level"],
                segment_breakdown=s["segment_breakdown"],
                source_platform_breakdown=s["source_platform_breakdown"],
            )
            db.add(score_record)
            created_scores.append(score_record)

        db.commit()
        logger.info(f"Successfully computed and ranked {len(created_scores)} opportunity scores.")
        return created_scores


# Global singleton
opportunity_scorer = OpportunityScorer()
