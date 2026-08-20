from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class RawScrapedDocument:
    """Standardized document payload extracted by an ingestion adapter before normalization."""
    source_platform: str  # reddit | playstore | appstore | youtube | twitter | forum | ecommerce
    content_text: str
    source_url: Optional[str] = None
    source_subreddit: Optional[str] = None
    author_id_hash: Optional[str] = None
    engagement_score: int = 0
    source_timestamp: Optional[datetime] = None
    content_language: str = "en"
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract base class for multi-source data ingestion scrapers."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the source platform (e.g. 'playstore', 'appstore', 'reddit')."""
        pass

    @abstractmethod
    def fetch(self, limit: int = 100, **kwargs) -> List[RawScrapedDocument]:
        """Fetch raw documents from the external source up to the specified limit.

        Args:
            limit: Maximum number of records to retrieve.
            **kwargs: Platform-specific options (e.g. app_id, subreddits, query terms).

        Returns:
            List of RawScrapedDocument instances.
        """
        pass
