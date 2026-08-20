import re
import hashlib
from html import unescape
from typing import Optional, Tuple


class TextNormalizer:
    """Normalizes raw unstructured user text, strips noise, and computes deterministic content hashes."""

    # Precompiled regex patterns for efficiency
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
    URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
    MULTI_SPACE_PATTERN = re.compile(r"[ \t]+")
    MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")
    NON_PRINTABLE_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

    def __init__(self, min_length: int = 15, max_length: int = 4000):
        self.min_length = min_length
        self.max_length = max_length

    def clean_text(self, text: Optional[str]) -> str:
        """Strip HTML, unescape entities, clean whitespace, and normalize text."""
        if not text:
            return ""

        # Unescape HTML entities (e.g., &amp; -> &, &#39; -> ')
        cleaned = unescape(text)

        # Remove HTML tags
        cleaned = self.HTML_TAG_PATTERN.sub(" ", cleaned)

        # Remove control / non-printable characters
        cleaned = self.NON_PRINTABLE_PATTERN.sub("", cleaned)

        # Normalize horizontal whitespace
        cleaned = self.MULTI_SPACE_PATTERN.sub(" ", cleaned)

        # Normalize excessive newlines
        cleaned = self.MULTI_NEWLINE_PATTERN.sub("\n\n", cleaned)

        return cleaned.strip()

    def compute_content_hash(self, text: str) -> str:
        """Compute deterministic SHA-256 hash for deduplication."""
        # Lowercase and strip all excessive spacing before hashing
        canonical_str = " ".join(text.lower().split())
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def is_valid_content(self, text: str) -> bool:
        """Check if text meets minimum length and basic character heuristics."""
        if not text:
            return False

        stripped = text.strip()
        if len(stripped) < self.min_length:
            return False

        # Filter out strings with no alphanumeric characters
        alpha_count = sum(1 for c in stripped if c.isalnum())
        if alpha_count < 10:
            return False

        return True

    def normalize(self, text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Clean, validate, truncate, and compute hash for text.

        Returns:
            Tuple of (normalized_text, content_hash) or (None, None) if invalid.
        """
        cleaned = self.clean_text(text)

        if not self.is_valid_content(cleaned):
            return None, None

        # Truncate if exceeds max length
        if len(cleaned) > self.max_length:
            cleaned = cleaned[: self.max_length].rstrip() + "..."

        content_hash = self.compute_content_hash(cleaned)
        return cleaned, content_hash

    def verify_verbatim_quote(self, quote: Optional[str], source_text: Optional[str]) -> bool:
        """Validate whether an extracted quote is a genuine verbatim substring of source text."""
        if not quote or not source_text:
            return False

        clean_q = " ".join(self.clean_text(quote).lower().split())
        clean_s = " ".join(self.clean_text(source_text).lower().split())

        if not clean_q or not clean_s:
            return False

        # Direct substring match on canonicalized strings
        return clean_q in clean_s


# Global singleton instance
normalizer = TextNormalizer()
