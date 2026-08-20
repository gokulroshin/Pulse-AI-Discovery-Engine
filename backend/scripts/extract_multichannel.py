import os
import sys
import re
import logging
from typing import List, Dict, Any, Optional

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.document import RawDocument
from app.models.extraction import Extraction
from app.models.pipeline_run import PipelineRun

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pulse.extract_multichannel")

# Causal patterns for extracting customer friction, hesitation, comparison, and motivation
CAUSAL_PATTERNS = [
    # Sizing & Fit
    (
        r"(?:size|sizing|fit|fitting|chest|waist|bust|length)\s+(?:is|was|felt|seemed|turned out)\s+(?:completely\s+)?(?:off|small|tight|loose|large|inaccurate|terrible|huge|weird|horrible)",
        "Fit and sizing discrepancy with inaccurate size chart specifications",
        "friction",
        "fit_sizing_discrepancy"
    ),
    (
        r"(?:bought|ordered|received|tried)\s+(?:size\s+[a-z0-9]+|m|l|xl|s|xs)\s+(?:but|and)\s+(?:it|the)\s+(?:was|fit|fitted)\s+(?:like|too|way too)\s+(?:tight|loose|small|big|short|long)",
        "Sizing inconsistency and unpredictable brand fit variations",
        "friction",
        "sizing_inconsistency"
    ),
    # Fabric & Photo fidelity
    (
        r"(?:color|fabric|cloth|material|quality|print|pattern)\s+(?:looked|looks|shown|in photos?)\s+(?:so|very\s+)?(?:bright|good|different|better|premium)\s+(?:but|however|whereas)\s+(?:in real(?:ity)?|actual|received)\s+(?:it|is|was)\s+(?:faded|dull|cheap|synthetic|rough|poor|translucent|thin)",
        "Catalog lighting and photo fidelity mismatch compared to real-world fabric texture",
        "uncertainty",
        "photo_reality_mismatch"
    ),
    (
        r"(?:looked at|checked|watched|searched for)\s+(?:youtube|instagram|reddit|haul|video|reviews?)\s+(?:to see|before buying|for actual|to check|try-?on)",
        "Seeking external video proof and unedited try-on feedback before purchasing",
        "external_validation",
        "off_platform_video_proof"
    ),
    # Returns & Customer Support
    (
        r"(?:return|exchange|refund|pickup|pick up)\s+(?:took|delayed|refused|rejected|pending|cancelled|failed|customer support|support team)",
        "Severe friction in return pickup coordination and delayed refund crediting",
        "friction",
        "return_refund_delays"
    ),
    (
        r"(?:customer care|support|executive|helpline|chat)\s+(?:was|is|gave|no help|unhelpful|useless|pathetic|rude|automated|bot|never resolved)",
        "Ineffective customer support and repetitive unhelpful automated responses",
        "friction",
        "customer_support_friction"
    ),
    # Wishlist & Postponement
    (
        r"(?:wishlisted|wishlist|shortlist(?:ed)?|saved)\s+(?:items?|products?|tops?|kurtas?|dresses?|shoes?)\s+(?:waiting for|waiting|to compare|to check|till|hoping for)\s+(?:sales?|discounts?|price drop|event|peer|reviews?)",
        "Using wishlist as temporary holding buffer while waiting for social validation or sales",
        "behavior",
        "wishlist_decision_deferral"
    ),
    (
        r"(?:compared?|comparing|shortlisted?)\s+(?:between|with|across|multiple)\s+(?:options?|products?|brands?|items?|sites?|ajio|myntra)",
        "Cross-comparing multiple shortlisted items across specs and platforms",
        "comparison",
        "multi_product_comparison"
    ),
    # Order cancellations
    (
        r"(?:cancelled|canceled|shortage|out of stock)\s+(?:after|post|days later|without notice|automatically|abruptly)",
        "Unexpected post-confirmation order cancellation and inventory sync failure",
        "friction",
        "post_order_cancellation"
    ),
    # Delivery tracking
    (
        r"(?:delivery|tracking|courier|shipment)\s+(?:delayed|late|fake attempt|wrong status|stuck|not delivered)",
        "Inaccurate delivery status updates and deceptive fake delivery attempt notices",
        "friction",
        "delivery_tracking_issues"
    ),
    # Styling & Occasion
    (
        r"(?:styling|outfit|matching|pair(?:ing)?|look|dupatta|accessories|occasion|wedding|festive)\s+(?:coordination|ideas?|suggestions?|complete|needed)",
        "Incomplete outfit styling context and accessory coordination guidance",
        "uncertainty",
        "styling_context_deficit"
    ),
]


def extract_from_channel_docs(platform: str, max_docs: int = 400, session: Optional[Any] = None):
    should_close = False
    if session is not None:
        db = session
    else:
        db = SessionLocal()
        should_close = True

    try:
        # Check docs from this platform without extractions
        extracted_subquery = db.query(Extraction.doc_id).distinct().subquery()
        unextracted_docs = (
            db.query(RawDocument)
            .filter(RawDocument.source_platform == platform)
            .filter(~RawDocument.doc_id.in_(extracted_subquery.select()))
            .limit(max_docs)
            .all()
        )

        logger.info(f"Processing {len(unextracted_docs)} unextracted {platform.upper()} documents...")

        extracted_count = 0
        for doc in unextracted_docs:
            content = doc.content_text or ""
            if len(content.strip()) < 20:
                continue

            found_reasons = []
            sentences = re.split(r'[.!?\n]+', content)

            for sentence in sentences:
                s_clean = sentence.strip()
                if len(s_clean) < 15:
                    continue

                for pattern, reason_desc, sig_type, cluster_hint in CAUSAL_PATTERNS:
                    if re.search(pattern, s_clean, re.IGNORECASE):
                        found_reasons.append({
                            "reason_text": reason_desc,
                            "verbatim_quote": s_clean[:250],
                            "confidence": "high" if len(s_clean) > 30 else "medium",
                            "signal_type": sig_type,
                            "preliminary_cluster_hint": cluster_hint,
                        })
                        break  # Match one pattern per sentence

            # If no pattern matched but doc is substantial, extract general sentence
            if not found_reasons and len(content) > 60:
                first_sent = sentences[0].strip() if sentences else content[:100]
                if len(first_sent) > 20:
                    found_reasons.append({
                        "reason_text": f"Consumer feedback regarding {doc.inferred_category or 'fashion'} shopping experience",
                        "verbatim_quote": first_sent[:250],
                        "confidence": "medium",
                        "signal_type": "friction" if any(w in content.lower() for w in ["bad", "poor", "issue", "worst", "waste"]) else "behavior",
                        "preliminary_cluster_hint": "general_experience",
                    })

            for r in found_reasons:
                ext = Extraction(
                    doc_id=doc.doc_id,
                    reason_text=r["reason_text"],
                    verbatim_quote=r["verbatim_quote"],
                    confidence=r["confidence"],
                    signal_type=r["signal_type"],
                    preliminary_cluster_hint=r["preliminary_cluster_hint"],
                )
                db.add(ext)
                extracted_count += 1

        db.commit()
        logger.info(f"Successfully extracted {extracted_count} reasons from {platform.upper()} documents.")

    finally:
        if should_close:
            db.close()


def main():
    logger.info("Extracting multi-channel qualitative reasons from Reddit, App Store, and YouTube...")
    extract_from_channel_docs("reddit", max_docs=400)
    extract_from_channel_docs("appstore", max_docs=250)
    extract_from_channel_docs("youtube", max_docs=100)
    logger.info("Multi-channel extraction complete.")


if __name__ == "__main__":
    main()
