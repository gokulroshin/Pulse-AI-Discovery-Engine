import logging
import hashlib
import time
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.ingestion.base_scraper import BaseScraper, RawScrapedDocument

logger = logging.getLogger("pulse.ingestion.reddit")

DEFAULT_SUBREDDITS = [
    "IndianFashionAddicts",
    "TwoXIndia",
    "india",
    "IndianSkincareAddicts",
]

DEFAULT_QUERIES = [
    "myntra wishlist",
    "myntra cart",
    "myntra sizing",
    "myntra fit",
    "myntra quality",
    "ajio wishlist",
    "buy or pass",
    "worth buying",
    "sizing help",
]


class RedditScraper(BaseScraper):
    """Fetches public Reddit discussions and comments on fashion wishlist & purchasing behavior."""

    @property
    def platform_name(self) -> str:
        return "reddit"

    def fetch_via_praw(
        self,
        limit: int = 200,
        subreddits: Optional[List[str]] = None,
        queries: Optional[List[str]] = None,
    ) -> List[RawScrapedDocument]:
        """Fetch Reddit discussions using PRAW if credentials are provided."""
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "PulseFashionDiscovery/1.0")

        if not client_id or not client_secret:
            return []

        documents = []
        try:
            import praw
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            target_subs = subreddits or DEFAULT_SUBREDDITS
            target_queries = queries or DEFAULT_QUERIES

            per_sub = max(5, limit // len(target_subs))
            for sub_name in target_subs:
                subreddit = reddit.subreddit(sub_name)
                for query in target_queries:
                    if len(documents) >= limit:
                        break
                    for post in subreddit.search(query, sort="relevance", limit=10):
                        title = post.title or ""
                        body = post.selftext or ""
                        full_text = f"{title}\n\n{body}".strip()
                        if not full_text:
                            continue

                        author_str = str(post.author) if post.author else "anonymous"
                        author_hash = hashlib.sha256(author_str.encode("utf-8")).hexdigest()[:16]
                        ts = datetime.fromtimestamp(post.created_utc, timezone.utc) if post.created_utc else None

                        doc = RawScrapedDocument(
                            source_platform="reddit",
                            content_text=full_text,
                            source_url=f"https://reddit.com{post.permalink}",
                            source_subreddit=f"r/{sub_name}",
                            author_id_hash=author_hash,
                            engagement_score=int(post.score or 0),
                            source_timestamp=ts,
                            content_language="en",
                            raw_metadata={"reddit_id": post.id, "num_comments": post.num_comments},
                        )
                        documents.append(doc)
        except Exception as e:
            logger.warning(f"PRAW fetching error: {e}")

        return documents

    def fetch(
        self,
        limit: int = 200,
        subreddits: Optional[List[str]] = None,
        queries: Optional[List[str]] = None,
        fetch_comments: bool = True,
        **kwargs
    ) -> List[RawScrapedDocument]:
        """Fetch Reddit posts and comments."""
        # 1. Try PRAW first if credentials exist
        praw_docs = self.fetch_via_praw(limit=limit, subreddits=subreddits, queries=queries)
        if praw_docs:
            logger.info(f"Reddit scraper fetched {len(praw_docs)} posts via PRAW.")
            return praw_docs

        # 2. Try public JSON endpoints with User-Agent
        documents: List[RawScrapedDocument] = []
        target_subs = subreddits or DEFAULT_SUBREDDITS
        target_queries = queries or DEFAULT_QUERIES

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        per_sub_limit = max(10, limit // len(target_subs))

        with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
            for subreddit in target_subs:
                sub_docs_count = 0
                for query in target_queries:
                    if sub_docs_count >= per_sub_limit or len(documents) >= limit:
                        break

                    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&sort=relevance&limit=25"
                    try:
                        time.sleep(1.0)
                        resp = client.get(url)
                        if resp.status_code != 200:
                            break

                        data = resp.json()
                        children = data.get("data", {}).get("children", [])
                        for child in children:
                            post_data = child.get("data", {})
                            title = post_data.get("title", "")
                            selftext = post_data.get("selftext", "")
                            permalink = post_data.get("permalink", "")
                            author = post_data.get("author", "anonymous")
                            score = post_data.get("score", 0)
                            created_utc = post_data.get("created_utc")

                            content_parts = [title]
                            if selftext and selftext not in ["[removed]", "[deleted]"]:
                                content_parts.append(selftext)

                            full_text = "\n\n".join(content_parts).strip()
                            if not full_text:
                                continue

                            author_hash = hashlib.sha256(author.encode("utf-8")).hexdigest()[:16]
                            post_timestamp = (
                                datetime.fromtimestamp(created_utc, timezone.utc)
                                if created_utc
                                else None
                            )

                            doc = RawScrapedDocument(
                                source_platform="reddit",
                                content_text=full_text,
                                source_url=f"https://reddit.com{permalink}" if permalink else None,
                                source_subreddit=f"r/{subreddit}",
                                author_id_hash=author_hash,
                                engagement_score=int(score or 0),
                                source_timestamp=post_timestamp,
                                content_language="en",
                                raw_metadata={
                                    "reddit_id": post_data.get("id"),
                                    "num_comments": post_data.get("num_comments", 0),
                                },
                            )
                            documents.append(doc)
                            sub_docs_count += 1

                    except Exception as e:
                        logger.debug(f"Error querying Reddit public endpoint for '{query}' in r/{subreddit}: {e}")
                        break

        logger.info(f"Reddit scraper fetched a total of {len(documents)} raw documents.")
        return documents
