import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.ingestion.base_scraper import BaseScraper, RawScrapedDocument

logger = logging.getLogger("pulse.ingestion.playstore")

# Target e-commerce fashion apps in India
DEFAULT_PLAYSTORE_APPS = {
    "myntra": "com.myntra.android",
    "ajio": "com.ril.ajio",
    "nykaa_fashion": "com.nykaa.fashion",
    "tatacliq": "com.tul.tatacliq",
    "amazon_fashion": "in.amazon.mShop.android.shopping",
}


class PlayStoreScraper(BaseScraper):
    """Fetches user reviews from Google Play Store for fashion e-commerce apps."""

    @property
    def platform_name(self) -> str:
        return "playstore"

    def fetch(
        self,
        limit: int = 200,
        apps: Optional[List[str]] = None,
        country: str = "in",
        lang: str = "en",
        filter_score_with: Optional[int] = None,
        **kwargs
    ) -> List[RawScrapedDocument]:
        """Fetch Play Store reviews using google-play-scraper."""
        documents: List[RawScrapedDocument] = []
        target_app_ids = []

        if apps:
            for app in apps:
                target_app_ids.append(DEFAULT_PLAYSTORE_APPS.get(app, app))
        else:
            target_app_ids = list(DEFAULT_PLAYSTORE_APPS.values())

        try:
            from google_play_scraper import reviews, Sort

            per_app_limit = max(10, limit // len(target_app_ids))

            for app_id in target_app_ids:
                logger.info(f"Fetching Play Store reviews for app_id: {app_id} (limit={per_app_limit})...")
                try:
                    result, _ = reviews(
                        app_id,
                        lang=lang,
                        country=country,
                        sort=Sort.MOST_RELEVANT,
                        count=per_app_limit,
                        filter_score_with=filter_score_with,
                    )

                    for item in result:
                        content = item.get("content", "")
                        if not content:
                            continue

                        user_name = item.get("userName", "anonymous")
                        author_hash = hashlib.sha256(user_name.encode("utf-8")).hexdigest()[:16]
                        thumbs_up = item.get("thumbsUpCount", 0)
                        review_date = item.get("at")
                        score = item.get("score", 0)

                        doc = RawScrapedDocument(
                            source_platform="playstore",
                            content_text=content,
                            source_url=f"https://play.google.com/store/apps/details?id={app_id}",
                            author_id_hash=author_hash,
                            engagement_score=int(thumbs_up or 0),
                            source_timestamp=review_date if isinstance(review_date, datetime) else None,
                            content_language=lang,
                            raw_metadata={
                                "app_id": app_id,
                                "star_rating": score,
                                "review_id": item.get("reviewId"),
                            },
                        )
                        documents.append(doc)

                except Exception as e:
                    logger.warning(f"Failed fetching reviews for Play Store app {app_id}: {e}")

        except ImportError:
            logger.error("google-play-scraper is not installed. Please install via pip.")

        logger.info(f"Play Store scraper fetched a total of {len(documents)} raw documents.")
        return documents
