import re
from typing import Dict, Any, Optional, Tuple


class MetadataEnricher:
    """Enriches raw document content with heuristic domain metadata tags."""

    # Keyword dictionaries for category inference
    CATEGORY_KEYWORDS = {
        "ethnic_wear": [
            r"\bkurta\b", r"\bkurti\b", r"\bkurtas\b", r"\bkurtis\b", r"\bsaree\b", r"\bsaris?\b",
            r"\blehenga\b", r"\banarkali\b", r"\bdupatta\b", r"\bsherwani\b", r"\bsalwar\b",
            r"\bpalazzos?\b", r"\bethnic\b", r"\bjhumkas?\b", r"\bchikankari\b", r"\bbandhani\b"
        ],
        "western": [
            r"\bdress(?:es)?\b", r"\bjeans\b", r"\btops?\b", r"\bt-?shirts?\b", r"\btees?\b",
            r"\bshirts?\b", r"\bblazers?\b", r"\bskirts?\b", r"\btrousers?\b", r"\bpants?\b",
            r"\bhoodies?\b", r"\bjackets?\b", r"\bdenim\b", r"\bco-?ord\b", r"\bjumpsuits?\b",
            r"\bsweaters?\b", r"\bcardigans?\b", r"\bcrop top\b"
        ],
        "footwear": [
            r"\bshoes?\b", r"\bsneakers?\b", r"\bheels?\b", r"\bboots?\b", r"\bflats\b",
            r"\bsandals?\b", r"\bloafers?\b", r"\bslippers?\b", r"\bfootwear\b", r"\bwedges\b",
            r"\bslides?\b", r"\bcrocs\b"
        ],
        "accessories": [
            r"\bbags?\b", r"\bhandbags?\b", r"\bbackpacks?\b", r"\bwallets?\b", r"\bwatch(?:es)?\b",
            r"\bsunglasses\b", r"\bjewelry\b", r"\bjewellery\b", r"\bearrings?\b", r"\bnecklaces?\b",
            r"\bbelts?\b", r"\bperfumes?\b"
        ],
    }

    # Keyword dictionaries for gender context inference
    GENDER_KEYWORDS = {
        "women": [
            r"\bwomen\b", r"\bwoman\b", r"\bgirls?\b", r"\blad(?:y|ies)\b", r"\bfemale\b",
            r"\bkurti\b", r"\bsaree\b", r"\blehenga\b", r"\bdress\b", r"\bbra\b", r"\bheels\b",
            r"\bherself\b", r"\bmother\b", r"\bsister\b", r"\bgirlfriend\b", r"\bwife\b"
        ],
        "men": [
            r"\bmen\b", r"\bman\b", r"\bguys?\b", r"\bmale\b", r"\bboys?\b",
            r"\bhimself\b", r"\bfather\b", r"\bbrother\b", r"\bboyfriend\b", r"\bhusband\b",
            r"\bsherwani\b", r"\bbeard\b", r"\bboxers\b"
        ],
        "unisex": [
            r"\bunisex\b", r"\bgender-?neutral\b", r"\ball-?gender\b", r"\bcouple\b"
        ]
    }

    # Keyword dictionaries for brand tier inference
    # Note: For words that collide with common English terms (ONLY, W, GAP), we require contextual markers or exact casing.
    BRAND_TIERS = {
        "premium": [
            r"\bzara\b", r"\bh&m\b", r"\blevi'?s\b", r"\bcalvin klein\b",
            r"\btommy hilfiger\b", r"\bsuperdry\b", r"\bted baker\b", r"\bfossil\b",
            r"\bmichael kors\b", r"\bmarks & spencer\b", r"\bforever new\b", r"\bnike\b",
            r"\badidas\b", r"\bpuma\b", r"\bmango\s+(?:clothing|dress|top|jeans|brand|store)\b",
            r"\bbrand\s+mango\b", r"\b(gap\s+(?:hoodie|jeans|t-?shirt|brand)|brand\s+gap)\b"
        ],
        "mid": [
            r"\broadster\b", r"\bhrx\b", r"\bvero moda\b",
            r"\b(only\s+(?:brand|dress|top|jeans|clothing|store)|brand\s+only)\b",
            r"\b(w\s+for\s+woman|w\s+brand|brand\s+w|w\s+kurti|w\s+store|w\s+clothing)\b",
            r"\bbiba\b", r"\blibas\b", r"\baurelia\b", r"\bfabindia\b", r"\bglobal desi\b",
            r"\bflying machine\b", r"\ballen solly\b", r"\bvan heusen\b", r"\blouis philippe\b",
            r"\buspa\b", r"\bsnitch\b", r"\bbewakoof\b"
        ],
        "value": [
            r"\banouk\b", r"\bmast & harbour\b", r"\bdressberry\b", r"\btokyo talkies\b",
            r"\bsangria\b", r"\bhere\s*&?\s*now\b", r"\bhighlander\b", r"\blocomotive\b"
        ]
    }

    # Strict case-sensitive brand acronyms checked on original text
    CASE_SENSITIVE_BRANDS = {
        "premium": [r"\bGAP\b", r"\bMANGO\b"],
        "mid": [r"\bONLY\b", r"\bW\b", r"\bUSPA\b", r"\bHRX\b"],
    }

    def infer_category(self, text: str) -> str:
        """Infer fashion product category from text mentions."""
        text_lower = text.lower()
        counts: Dict[str, int] = {}

        for category, patterns in self.CATEGORY_KEYWORDS.items():
            count = sum(1 for pattern in patterns if re.search(pattern, text_lower))
            if count > 0:
                counts[category] = count

        if not counts:
            return "general"

        # Return category with highest keyword hit count
        return max(counts, key=counts.get)

    def infer_gender_context(self, text: str) -> str:
        """Infer target gender context from user language and product references."""
        text_lower = text.lower()
        women_hits = sum(1 for p in self.GENDER_KEYWORDS["women"] if re.search(p, text_lower))
        men_hits = sum(1 for p in self.GENDER_KEYWORDS["men"] if re.search(p, text_lower))
        unisex_hits = sum(1 for p in self.GENDER_KEYWORDS["unisex"] if re.search(p, text_lower))

        if unisex_hits > 0 and unisex_hits >= women_hits and unisex_hits >= men_hits:
            return "unisex"
        if women_hits > men_hits:
            return "women"
        if men_hits > women_hits:
            return "men"
        if women_hits > 0 and men_hits > 0:
            return "unisex"

        return "unknown"

    def infer_brand_tier(self, text: str) -> str:
        """Infer brand price tier from mentioned fashion labels with collision resistance."""
        text_lower = text.lower()

        # 1. Standard regex matching on lowercase text
        for tier, patterns in self.BRAND_TIERS.items():
            if any(re.search(pattern, text_lower) for pattern in patterns):
                return tier

        # 2. Case-sensitive matching on original text for acronyms (ONLY, GAP, W)
        for tier, patterns in self.CASE_SENSITIVE_BRANDS.items():
            if any(re.search(pattern, text) for pattern in patterns):
                return tier

        return "unknown"

    def enrich(self, text: str, initial_score: int = 0) -> Dict[str, Any]:
        """Perform complete heuristic metadata enrichment on document text."""
        return {
            "inferred_category": self.infer_category(text),
            "inferred_gender_context": self.infer_gender_context(text),
            "inferred_brand_tier": self.infer_brand_tier(text),
            "engagement_score": max(0, int(initial_score)),
        }


# Global singleton instance
metadata_enricher = MetadataEnricher()
