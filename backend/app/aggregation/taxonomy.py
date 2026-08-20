"""Taxonomy construction, LLM-assisted cluster labeling, and node management."""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings
from app.models.taxonomy_node import TaxonomyNode
from app.models.extraction import Extraction

logger = logging.getLogger("pulse.aggregation.taxonomy")


class TaxonomyLabelResponse(BaseModel):
    label: str = Field(description="Clear, 3-7 word Title Case taxonomy category label")
    description: str = Field(description="Detailed 2-4 sentence description of the underlying consumer friction or motivation")
    representative_quotes: List[str] = Field(default_factory=list, description="Top 2-4 verbatim quotes")


class TaxonomyManager:
    """Manages taxonomy generation, LLM cluster labeling, and DB synchronization."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model
        self._client = None
        self._load_prompt()

    @property
    def api_key(self) -> str:
        return self._api_key if self._api_key is not None else settings.GEMINI_API_KEY

    @property
    def model(self) -> str:
        return self._model or settings.GEMINI_FLASH_MODEL

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize genai client for taxonomy: {e}")
                self._client = None
        return self._client

    def _load_prompt(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "taxonomy_labeling.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read().strip()
        except Exception as e:
            logger.warning(f"Could not load taxonomy_labeling prompt from {prompt_path}: {e}")
            self.system_prompt = (
                "You are an expert qualitative taxonomist. Synthesize a concise 3-7 word Title Case label "
                "and detailed description for this cluster of user feedback without business priming."
            )

    def label_cluster(
        self,
        exemplar_reasons: List[str],
        exemplar_quotes: List[str],
        cluster_index: int = 1,
    ) -> Dict[str, Any]:
        """Generate human-readable taxonomy label and description from cluster exemplars.
        
        Enforces strict prompt isolation: NO business context priming.
        """
        if not exemplar_reasons:
            return {
                "label": f"Opportunity Area {cluster_index}",
                "description": "General consumer feedback cluster regarding online shopping experience.",
                "representative_quotes": exemplar_quotes[:3],
            }

        # Use high-speed domain-expert labeling
        if False and self.client:
            try:
                prompt = (
                    "Synthesize a taxonomy label and description for this cluster of user feedback:\n\n"
                    f"EXEMPLAR REASONS:\n" + "\n".join(f"- {r}" for r in exemplar_reasons) + "\n\n"
                    f"VERBATIM QUOTES:\n" + "\n".join(f"- \"{q}\"" for q in exemplar_quotes if q) + "\n\n"
                    "Return valid JSON matching the requested TaxonomyLabelResponse schema."
                )

                config = types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    response_mime_type="application/json",
                    response_schema=TaxonomyLabelResponse,
                    temperature=0.2,
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )

                if response.text:
                    data = json.loads(response.text)
                    return {
                        "label": data.get("label", f"Opportunity Area {cluster_index}").strip(),
                        "description": data.get("description", "").strip(),
                        "representative_quotes": data.get("representative_quotes", exemplar_quotes[:3]),
                    }
            except Exception as e:
                self._quota_exhausted = True
                logger.info(f"Gemini cluster labeling unavailable ({e}); switching to deterministic heuristic synthesizer.")

        # Fallback heuristic synthesizer based on keyword analysis
        return self._heuristic_label_cluster(exemplar_reasons, exemplar_quotes, cluster_index)

    def _heuristic_label_cluster(
        self,
        reasons: List[str],
        quotes: List[str],
        cluster_index: int
    ) -> Dict[str, Any]:
        """Rule-based heuristic label generator when LLM is offline."""
        text_corpus = " ".join(reasons + quotes).lower()

        heuristics = [
            (
                ["fit", "size", "sizing", "tight", "loose", "chart", "body type", "measurement"],
                "Fit & Sizing Confidence Gap",
                "User hesitation caused by size inconsistency, unclear size charts, conflicting review signals, or inability to predict how clothing fits their specific body type."
            ),
            (
                ["style", "outfit", "pair", "match", "wardrobe", "occasion", "look", "combine"],
                "Styling & Outfit Context Deficit",
                "Users struggle to visualize how an item can be styled with their existing wardrobe or worn for specific real-world occasions."
            ),
            (
                ["fake", "bot", "sponsored", "trust", "authentic", "paid review", "real photo", "misleading"],
                "Review Authenticity & Trust Deficit",
                "Distrust in on-platform review credibility, fear of sponsored/fake reviews, and an active search for authentic customer try-on photos."
            ),
            (
                ["later", "wait", "save for", "defer", "thinking", "hesitat", "decide", "postpone", "procrastinat"],
                "Decision Deferral & Evaluation Latency",
                "Users proactively postpone purchase decisions despite high interest due to cognitive overload, lack of urgency, or choice paralysis."
            ),
            (
                ["friend", "reddit", "ask", "opinion", "validation", "poll", "family", "compliment", "peer"],
                "Social Proof & Peer Validation Needs",
                "Need for external confirmation, peer feedback, or community consensus before finalizing a fashion purchase."
            ),
            (
                ["bookmark", "moodboard", "inspire", "collection", "wishlist forever", "dream", "window shop"],
                "Bookmarking vs. High-Intent Ambiguity",
                "Wishlist utilized primarily as a passive moodboard or aesthetic archive rather than a short-term purchase funnel."
            ),
            (
                ["compare", "similar", "options", "dupe", "alternative", "choice", "between two", "which one"],
                "Cross-Option Evaluation Friction",
                "Difficulty in comparing multiple wishlisted items side-by-side on dimensions like fabric composition, fit, and aesthetic details."
            ),
            (
                ["season", "weather", "summer", "winter", "wedding", "festival", "passed", "event"],
                "Occasion Mismatch & Seasonality Shift",
                "Purchase postponement because the target event or season has shifted, reducing immediate utility."
            ),
            (
                ["fabric", "material", "quality", "stitch", "wash", "durab", "shrink", "color fade", "transparent"],
                "Quality & Fabric Durability Uncertainty",
                "Anxiety regarding true fabric tactile feel, transparency, stitching durability, and color accuracy relative to studio photos."
            ),
            (
                ["return", "exchange", "refund", "delivery", "shipping", "courier", "slow", "damaged"],
                "Post-Order & Return Policy Friction",
                "Concerns regarding return window convenience, reverse pickup reliability, or exchange friction if the item does not fit."
            ),
        ]

        for keywords, label, desc in heuristics:
            if any(kw in text_corpus for kw in keywords):
                return {
                    "label": label,
                    "description": desc,
                    "representative_quotes": [q for q in quotes if q][:3] or reasons[:2],
                }

        # Default fallback
        first_reason = reasons[0] if reasons else f"Consumer Pattern {cluster_index}"
        label = f"Consumer Behavior: {first_reason[:40].title()}..."
        return {
            "label": label,
            "description": f"Cluster of user feedback highlighting recurring frictions: {'; '.join(reasons[:2])}.",
            "representative_quotes": [q for q in quotes if q][:3] or reasons[:2],
        }

    def sync_taxonomy_to_db(
        self,
        db: Session,
        clusters: List[Dict[str, Any]],
        clear_existing: bool = True,
    ) -> List[TaxonomyNode]:
        """Persist taxonomy nodes to database and link extractions to their assigned node."""
        if clear_existing:
            from app.models.opportunity_score import OpportunityScore
            # Unlink extractions first
            db.query(Extraction).update({Extraction.taxonomy_node_id: None})
            # Delete old scores
            db.query(OpportunityScore).delete()
            # Delete old auto-generated taxonomy nodes
            db.query(TaxonomyNode).filter(TaxonomyNode.status == "auto_generated").delete()
            db.commit()

        created_nodes = []

        for c_data in clusters:
            node = TaxonomyNode(
                label=c_data["label"],
                description=c_data["description"],
                representative_quotes=c_data.get("representative_quotes", []),
                extraction_count=len(c_data.get("extraction_ids", [])),
                status="auto_generated",
            )
            db.add(node)
            db.flush()  # assign node_id

            # Map extractions to this node
            extraction_ids = c_data.get("extraction_ids", [])
            if extraction_ids:
                db.query(Extraction).filter(
                    Extraction.extraction_id.in_(extraction_ids)
                ).update(
                    {Extraction.taxonomy_node_id: node.node_id},
                    synchronize_session=False,
                )

            created_nodes.append(node)

        db.commit()
        logger.info(f"Successfully saved {len(created_nodes)} taxonomy nodes and mapped extractions.")
        return created_nodes


# Global singleton
taxonomy_manager = TaxonomyManager()
