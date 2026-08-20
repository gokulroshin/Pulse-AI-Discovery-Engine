import csv
import io
import json
import logging
import hashlib
from typing import List, Dict, Any, Union, Optional
from datetime import datetime
from app.ingestion.base_scraper import BaseScraper, RawScrapedDocument

logger = logging.getLogger("pulse.ingestion.manual_upload")


class ManualUploadHandler(BaseScraper):
    """Processes uploaded CSV or JSON corpus files and structured payloads."""

    @property
    def platform_name(self) -> str:
        return "manual_upload"

    def parse_dict_item(self, item: Dict[str, Any], default_platform: str = "ecommerce") -> Optional[RawScrapedDocument]:
        """Convert a single dictionary record to RawScrapedDocument with case-insensitive key lookup."""
        # Create normalized lowercase dictionary for robust lookup
        norm_item = {
            str(k).strip().lstrip("\ufeff").lower(): v
            for k, v in item.items()
            if k is not None
        }

        # Find text field from common aliases
        content_text = (
            norm_item.get("content_text")
            or norm_item.get("text")
            or norm_item.get("review")
            or norm_item.get("comment")
            or norm_item.get("body")
            or norm_item.get("review_text")
            or norm_item.get("feedback")
        )
        if not content_text or not isinstance(content_text, str) or not content_text.strip():
            return None

        platform = norm_item.get("source_platform") or norm_item.get("platform") or default_platform
        author = norm_item.get("author") or norm_item.get("user") or norm_item.get("username") or "anonymous"
        author_hash = norm_item.get("author_id_hash") or hashlib.sha256(str(author).encode("utf-8")).hexdigest()[:16]

        score = norm_item.get("engagement_score") or norm_item.get("score") or norm_item.get("upvotes") or norm_item.get("likes") or 0
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0

        source_timestamp = None
        raw_ts = norm_item.get("source_timestamp") or norm_item.get("timestamp") or norm_item.get("date")
        if isinstance(raw_ts, datetime):
            source_timestamp = raw_ts
        elif isinstance(raw_ts, str):
            try:
                source_timestamp = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            except Exception:
                pass

        return RawScrapedDocument(
            source_platform=str(platform).lower(),
            content_text=content_text.strip(),
            source_url=norm_item.get("source_url") or norm_item.get("url"),
            source_subreddit=norm_item.get("source_subreddit") or norm_item.get("subreddit"),
            author_id_hash=author_hash,
            engagement_score=score,
            source_timestamp=source_timestamp,
            content_language=norm_item.get("content_language", "en"),
            raw_metadata=norm_item.get("raw_metadata", {}),
        )

    def parse_csv(self, file_content: Union[str, bytes], default_platform: str = "ecommerce") -> List[RawScrapedDocument]:
        """Parse raw CSV string/bytes into RawScrapedDocuments with UTF-8 BOM handling."""
        if isinstance(file_content, bytes):
            # utf-8-sig automatically strips BOM if present
            file_content = file_content.decode("utf-8-sig", errors="replace")
        elif isinstance(file_content, str):
            file_content = file_content.lstrip("\ufeff")

        documents: List[RawScrapedDocument] = []
        reader = csv.DictReader(io.StringIO(file_content))
        for row in reader:
            doc = self.parse_dict_item(row, default_platform=default_platform)
            if doc:
                documents.append(doc)

        logger.info(f"Manual upload parsed {len(documents)} documents from CSV.")
        return documents

    def parse_json(self, file_content: Union[str, bytes, List[Dict[str, Any]]], default_platform: str = "ecommerce") -> List[RawScrapedDocument]:
        """Parse JSON string, bytes, or Python list into RawScrapedDocuments with UTF-8 BOM handling."""
        data = file_content
        if isinstance(file_content, bytes):
            data = json.loads(file_content.decode("utf-8-sig", errors="replace"))
        elif isinstance(file_content, str):
            data = json.loads(file_content.lstrip("\ufeff"))

        if isinstance(data, dict) and "items" in data:
            data = data["items"]

        if not isinstance(data, list):
            raise ValueError("Expected JSON payload to be an array of objects or an object containing an 'items' array.")

        documents: List[RawScrapedDocument] = []
        for item in data:
            if isinstance(item, dict):
                doc = self.parse_dict_item(item, default_platform=default_platform)
                if doc:
                    documents.append(doc)

        logger.info(f"Manual upload parsed {len(documents)} documents from JSON.")
        return documents

    def fetch(self, limit: int = 100, **kwargs) -> List[RawScrapedDocument]:
        """BaseScraper fetch method — accepts raw file content or data payload."""
        data = kwargs.get("data")
        if not data:
            return []
        if isinstance(data, (list, dict)):
            return self.parse_json(data)
        elif isinstance(data, str) and (data.strip().startswith("{") or data.strip().startswith("[")):
            return self.parse_json(data)
        else:
            return self.parse_csv(data)


# Global singleton instance
manual_upload_handler = ManualUploadHandler()
