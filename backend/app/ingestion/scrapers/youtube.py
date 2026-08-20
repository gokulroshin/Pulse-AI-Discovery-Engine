import logging
import hashlib
import os
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.ingestion.base_scraper import BaseScraper, RawScrapedDocument

logger = logging.getLogger("pulse.ingestion.youtube")

# Fashion review / haul video IDs on Indian e-commerce (Myntra, AJIO haul/try-ons)
DEFAULT_FASHION_VIDEO_IDS = [
    "dQw4w9WgXcQ",  # Sample fallback
]


class YouTubeScraper(BaseScraper):
    """Fetches user comments on fashion review & try-on haul videos via YouTube Data API v3."""

    @property
    def platform_name(self) -> str:
        return "youtube"

    def fetch(
        self,
        limit: int = 100,
        video_ids: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> List[RawScrapedDocument]:
        """Fetch YouTube comments for target fashion haul/review videos."""
        documents: List[RawScrapedDocument] = []
        yt_api_key = api_key or os.getenv("YOUTUBE_API_KEY")

        if not yt_api_key:
            logger.info("YouTube API key not configured. Skipping live YouTube API calls.")
            return documents

        target_video_ids = video_ids or DEFAULT_FASHION_VIDEO_IDS
        per_video_limit = max(10, limit // len(target_video_ids))

        with httpx.Client(timeout=15.0) as client:
            for video_id in target_video_ids:
                url = "https://www.googleapis.com/youtube/v3/commentThreads"
                params = {
                    "part": "snippet",
                    "videoId": video_id,
                    "maxResults": min(100, per_video_limit),
                    "key": yt_api_key,
                    "textFormat": "plainText",
                }

                try:
                    resp = client.get(url, params=params)
                    if resp.status_code != 200:
                        logger.warning(f"YouTube API returned status {resp.status_code} for video {video_id}")
                        continue

                    data = resp.json()
                    items = data.get("items", [])

                    for item in items:
                        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                        text = snippet.get("textDisplay", "")
                        if not text:
                            continue

                        author = snippet.get("authorDisplayName", "anonymous")
                        author_hash = hashlib.sha256(author.encode("utf-8")).hexdigest()[:16]
                        like_count = snippet.get("likeCount", 0)
                        published_at = snippet.get("publishedAt")

                        source_timestamp = None
                        if published_at:
                            try:
                                source_timestamp = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                            except Exception:
                                pass

                        doc = RawScrapedDocument(
                            source_platform="youtube",
                            content_text=text,
                            source_url=f"https://www.youtube.com/watch?v={video_id}",
                            author_id_hash=author_hash,
                            engagement_score=int(like_count or 0),
                            source_timestamp=source_timestamp,
                            content_language="en",
                            raw_metadata={"video_id": video_id, "comment_id": item.get("id")},
                        )
                        documents.append(doc)

                except Exception as e:
                    logger.warning(f"Error fetching YouTube comments for video {video_id}: {e}")

        logger.info(f"YouTube scraper fetched {len(documents)} comments.")
        return documents
