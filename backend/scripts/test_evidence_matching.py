import os
import sys
import re
from typing import List, Dict, Any, Optional

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.extraction import Extraction
from app.models.document import RawDocument
from app.models.taxonomy_node import TaxonomyNode
from app.models.opportunity_score import OpportunityScore
from sqlalchemy import or_, and_, desc

def retrieve_top_evidence(
    db,
    question: str,
    target_terms: Optional[List[str]] = None,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 4
) -> List[Dict[str, Any]]:
    """Retrieve highly relevant verbatim quotes matching the specific question intent."""
    q_lower = question.lower()
    
    # 1. Determine search terms
    search_keywords = list(target_terms) if target_terms else []
    
    if not search_keywords:
        # Extract meaningful domain words
        raw_words = re.findall(r'\b[a-zA-Z]{3,}\b', q_lower)
        stopwords = {
            "what", "when", "where", "which", "does", "face", "users", "fashion", 
            "products", "item", "items", "user", "their", "about", "have", "with", 
            "while", "that", "this", "they", "from", "into", "after", "been", "being"
        }
        content_words = [w for w in raw_words if w not in stopwords]
        
        # Intent mapping for common question themes
        if any(w in content_words for w in ["prevent", "prevents", "stopping", "stop", "hurdle", "barrier", "abandon", "hesitate", "hesitation"]):
            search_keywords.extend(["size", "fit", "tight", "chart", "return", "refund", "cancel", "fabric", "exchange"])
        elif any(w in content_words for w in ["wishlist", "save", "saved", "bookmark", "defer", "postpone", "later", "intent"]):
            search_keywords.extend(["wishlist", "shortlist", "compare", "waiting", "sale", "discount", "styling", "reel", "look"])
        elif any(w in content_words for w in ["uncertainty", "uncertainties", "doubt", "worry", "color", "material", "texture", "real"]):
            search_keywords.extend(["fabric", "material", "photo", "lighting", "color", "daylight", "shine", "drape", "transparent", "shrink"])
        elif any(w in content_words for w in ["styling", "style", "outfit", "wear", "match", "pair"]):
            search_keywords.extend(["style", "outfit", "styling", "pair", "match", "dupatta", "jacket", "jeans", "accessories"])
        else:
            search_keywords.extend(content_words)

    # 2. Query extractions with relevance filtering
    query = db.query(Extraction, RawDocument).join(RawDocument, Extraction.doc_id == RawDocument.doc_id)
    
    if category:
        query = query.filter(RawDocument.inferred_category == category)
    if platform:
        query = query.filter(RawDocument.source_platform == platform)
        
    # Build search filters
    clauses = []
    for term in search_keywords[:10]:
        t_clean = term.strip().lower()
        if len(t_clean) >= 3:
            clauses.append(Extraction.verbatim_quote.ilike(f"%{t_clean}%"))
            clauses.append(Extraction.reason_text.ilike(f"%{t_clean}%"))
            
    if clauses:
        query = query.filter(or_(*clauses))
        
    candidates = query.order_by(desc(RawDocument.engagement_score)).limit(100).all()
    
    # 3. Score candidates by relevance to the specific question
    scored_items = []
    seen_quotes = set()
    
    for ext, doc in candidates:
        quote = (ext.verbatim_quote or "").strip()
        if not quote or len(quote) < 15 or quote in seen_quotes:
            continue
            
        quote_lower = quote.lower()
        reason_lower = (ext.reason_text or "").lower()
        
        # Calculate relevance score
        rel_score = 0
        
        # Check matching target terms
        for term in search_keywords:
            t = term.lower()
            if t in quote_lower:
                rel_score += 4
            if t in reason_lower:
                rel_score += 2
                
        # Negative penalty for generic/off-topic app bugs if question is about fashion/product/intent
        if any(bad in quote_lower for bad in ["search results", "back button", "downloaded the app because they advertised", "delivering in minutes", "delivery failed"]):
            if not any(good in q_lower for good in ["delivery", "tracking", "search", "navigation"]):
                rel_score -= 10
                
        if rel_score > 0:
            seen_quotes.add(quote)
            scored_items.append({
                "score": rel_score,
                "platform": doc.source_platform,
                "quote": quote,
                "reason": ext.reason_text,
                "url": doc.source_url
            })
            
    # Sort by relevance score
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    
    # 4. Multi-channel diversity selection
    selected = []
    used_platforms = set()
    
    # First pass: one best quote per platform
    for item in scored_items:
        if item["platform"] not in used_platforms and len(selected) < limit:
            selected.append(item)
            used_platforms.add(item["platform"])
            
    # Second pass: fill remaining slots with highest scoring items
    for item in scored_items:
        if len(selected) >= limit:
            break
        if item not in selected:
            selected.append(item)
            
    return selected

def test_questions():
    db = SessionLocal()
    try:
        q1 = "What prevents wishlisted products from eventually being purchased?"
        print(f"\n--- Testing Q1: {q1} ---")
        evidence1 = retrieve_top_evidence(
            db, 
            q1, 
            target_terms=["size", "fit", "tight", "chart", "return", "refund", "cancel", "fabric"]
        )
        for i, e in enumerate(evidence1, 1):
            print(f"[{i}] ({e['platform'].upper()}) (Score: {e['score']})\n    \"{e['quote']}\"\n    Reason: {e['reason']}")
            
        q2 = "Why do users add fashion products to their wishlist?"
        print(f"\n--- Testing Q2: {q2} ---")
        evidence2 = retrieve_top_evidence(
            db, 
            q2, 
            target_terms=["wishlist", "saved", "shortlist", "compare", "waiting", "sales", "styling", "reel"]
        )
        for i, e in enumerate(evidence2, 1):
            print(f"[{i}] ({e['platform'].upper()}) (Score: {e['score']})\n    \"{e['quote']}\"\n    Reason: {e['reason']}")
            
        q3 = "What uncertainties remain after users have identified a product they like?"
        print(f"\n--- Testing Q3: {q3} ---")
        evidence3 = retrieve_top_evidence(
            db, 
            q3, 
            target_terms=["fabric", "material", "photo", "lighting", "color", "daylight", "shine", "drape", "transparent", "video"]
        )
        for i, e in enumerate(evidence3, 1):
            print(f"[{i}] ({e['platform'].upper()}) (Score: {e['score']})\n    \"{e['quote']}\"\n    Reason: {e['reason']}")

    finally:
        db.close()

if __name__ == "__main__":
    test_questions()
