import logging
import hashlib
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.ingestion.base_scraper import BaseScraper, RawScrapedDocument

logger = logging.getLogger("pulse.ingestion.appstore")

# Target Apple App Store App IDs (India Store)
DEFAULT_APPSTORE_APPS = {
    "myntra": {"id": "907394059", "name": "Myntra: Online Fashion App"},
    "ajio": {"id": "1105991823", "name": "AJIO: Online Shopping App"},
    "nykaa_fashion": {"id": "1501170792", "name": "Nykaa Fashion - Shopping App"},
    "tatacliq": {"id": "1107575195", "name": "Tata CLiQ - Online Shopping"},
}


class AppStoreScraper(BaseScraper):
    """Fetches user reviews from Apple App Store via iTunes customer reviews API."""

    @property
    def platform_name(self) -> str:
        return "appstore"

    def fetch(
        self,
        limit: int = 200,
        apps: Optional[List[str]] = None,
        country: str = "in",
        **kwargs
    ) -> List[RawScrapedDocument]:
        """Fetch App Store customer reviews."""
        documents: List[RawScrapedDocument] = []
        target_apps = {}

        if apps:
            for app_key in apps:
                if app_key in DEFAULT_APPSTORE_APPS:
                    target_apps[app_key] = DEFAULT_APPSTORE_APPS[app_key]
                else:
                    target_apps[app_key] = {"id": app_key, "name": app_key}
        else:
            target_apps = DEFAULT_APPSTORE_APPS

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        per_app_limit = max(10, limit // len(target_apps))
        pages_to_fetch = min(10, (per_app_limit + 49) // 50)

        with httpx.Client(timeout=15.0, headers=headers) as client:
            for app_key, app_meta in target_apps.items():
                app_id = app_meta["id"]
                app_name = app_meta["name"]
                logger.info(f"Fetching App Store reviews for {app_name} (id={app_id}, pages={pages_to_fetch})...")

                count_for_app = 0
                for page in range(1, pages_to_fetch + 1):
                    if count_for_app >= per_app_limit:
                        break

                    url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/page={page}/json"
                    try:
                        resp = client.get(url)
                        if resp.status_code != 200:
                            logger.warning(f"App Store API returned status {resp.status_code} for {app_id} (page {page})")
                            break

                        data = resp.json()
                        feed = data.get("feed", {})
                        entries = feed.get("entry", [])

                        if not entries:
                            break

                        # When only 1 entry is returned, iTunes API returns a dict rather than list
                        if isinstance(entries, dict):
                            entries = [entries]

                        for entry in entries:
                            # Skip if content is missing
                            content_obj = entry.get("content", {})
                            content_text = content_obj.get("label", "")
                            title_obj = entry.get("title", {})
                            title_text = title_obj.get("label", "")

                            full_text = f"{title_text}: {content_text}" if title_text else content_text
                            if not full_text:
                                continue

                            author_obj = entry.get("author", {})
                            author_name = author_obj.get("name", {}).get("label", "anonymous")
                            author_hash = hashlib.sha256(author_name.encode("utf-8")).hexdigest()[:16]

                            rating_obj = entry.get("im:rating", {})
                            rating = int(rating_obj.get("label", "0")) if isinstance(rating_obj, dict) else 0

                            # Vote count if present
                            vote_obj = entry.get("im:voteCount", {})
                            vote_count = int(vote_obj.get("label", "0")) if isinstance(vote_obj, dict) else 0

                            doc = RawScrapedDocument(
                                source_platform="appstore",
                                content_text=full_text,
                                source_url=f"https://apps.apple.com/{country}/app/id{app_id}",
                                author_id_hash=author_hash,
                                engagement_score=vote_count,
                                content_language="en",
                                raw_metadata={
                                    "app_id": app_id,
                                    "app_name": app_name,
                                    "star_rating": rating,
                                    "review_id": entry.get("id", {}).get("label") if isinstance(entry.get("id"), dict) else None,
                                },
                            )
                            documents.append(doc)
                            count_for_app += 1

                    except Exception as e:
                        logger.warning(f"Error fetching page {page} for App Store app {app_id}: {e}")
                        break

        logger.info(f"App Store scraper fetched a total of {len(documents)} raw documents.")
        return documents
