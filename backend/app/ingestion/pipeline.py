import logging
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.pipeline_run import PipelineRun
from app.models.document import RawDocument
from app.ingestion.normalizer import normalizer
from app.ingestion.metadata_enricher import metadata_enricher
from app.ingestion.base_scraper import RawScrapedDocument
from app.ingestion.scrapers.playstore import PlayStoreScraper
from app.ingestion.scrapers.appstore import AppStoreScraper
from app.ingestion.scrapers.reddit import RedditScraper
from app.ingestion.scrapers.youtube import YouTubeScraper
from app.ingestion.scrapers.manual_upload import ManualUploadHandler

logger = logging.getLogger("pulse.ingestion.pipeline")


class IngestionPipeline:
    """Orchestrates multi-source scraping, text normalization, deduplication, and database persistence."""

    def __init__(self):
        self.scrapers = {
            "playstore": PlayStoreScraper(),
            "appstore": AppStoreScraper(),
            "reddit": RedditScraper(),
            "youtube": YouTubeScraper(),
            "manual_upload": ManualUploadHandler(),
        }

    def run(
        self,
        sources: Optional[List[str]] = None,
        limit_per_source: int = 200,
        db: Optional[Session] = None,
        config: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> PipelineRun:
        """Execute complete ingestion workflow.

        Args:
            sources: List of source platforms to scrape (e.g., ['playstore', 'appstore', 'reddit']).
            limit_per_source: Max documents to fetch per source.
            db: Optional active database session.
            config: Additional execution parameters.
            run_id: Existing PipelineRun ID to attach to, or None to create a new one.

        Returns:
            The completed PipelineRun instance.
        """
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        target_sources = sources or ["playstore", "appstore", "reddit"]
        exec_config = {
            "sources": target_sources,
            "limit_per_source": limit_per_source,
            **(config or {}),
        }

        # 1. Initialize or load PipelineRun record
        if run_id:
            pipeline_run = db.query(PipelineRun).filter_by(run_id=run_id).first()
            if pipeline_run:
                pipeline_run.status = "running"
                pipeline_run.config = exec_config
                db.commit()
            else:
                pipeline_run = PipelineRun(
                    run_id=run_id, stage="ingestion", status="running", config=exec_config, stats={}
                )
                db.add(pipeline_run)
                db.commit()
        else:
            pipeline_run = PipelineRun(
                stage="ingestion", status="running", config=exec_config, stats={}
            )
            db.add(pipeline_run)
            db.commit()
            db.refresh(pipeline_run)

        logger.info(f"Starting ingestion pipeline run [{pipeline_run.run_id}] for sources: {target_sources}")

        stats = {
            "total_fetched": 0,
            "total_normalized": 0,
            "total_duplicates": 0,
            "total_inserted": 0,
            "by_platform": {},
            "by_category": {},
            "errors": [],
        }

        try:
            all_raw_docs: List[RawScrapedDocument] = []

            # 2. Fetch from each configured source
            for source_name in target_sources:
                scraper = self.scrapers.get(source_name)
                if not scraper:
                    logger.warning(f"Unknown scraper source '{source_name}'. Skipping.")
                    continue

                stats["by_platform"][source_name] = {
                    "fetched": 0,
                    "inserted": 0,
                    "duplicates": 0,
                }

                try:
                    logger.info(f"Executing scraper: {source_name} (limit={limit_per_source})...")
                    docs = scraper.fetch(limit=limit_per_source, **(config or {}))
                    all_raw_docs.extend(docs)
                    stats["total_fetched"] += len(docs)
                    stats["by_platform"][source_name]["fetched"] = len(docs)
                except Exception as e:
                    err_msg = f"Error running scraper {source_name}: {str(e)}"
                    logger.error(err_msg)
                    stats["errors"].append(err_msg)

            # 3. Process documents (normalize, deduplicate, enrich, persist)
            new_db_documents: List[RawDocument] = []
            seen_hashes_in_batch = set()

            for raw_doc in all_raw_docs:
                platform_key = raw_doc.source_platform
                if platform_key not in stats["by_platform"]:
                    stats["by_platform"][platform_key] = {"fetched": 0, "inserted": 0, "duplicates": 0}

                # Normalization
                cleaned_text, content_hash = normalizer.normalize(raw_doc.content_text)
                if not cleaned_text or not content_hash:
                    continue  # Filtered out due to length or invalid content

                stats["total_normalized"] += 1

                # In-batch deduplication
                if content_hash in seen_hashes_in_batch:
                    stats["total_duplicates"] += 1
                    stats["by_platform"][platform_key]["duplicates"] += 1
                    continue

                seen_hashes_in_batch.add(content_hash)

                # Database deduplication check
                existing_doc = (
                    db.query(RawDocument.doc_id)
                    .filter_by(content_hash=content_hash)
                    .first()
                )
                if existing_doc:
                    stats["total_duplicates"] += 1
                    stats["by_platform"][platform_key]["duplicates"] += 1
                    continue

                # Heuristic metadata enrichment
                enriched = metadata_enricher.enrich(
                    cleaned_text, initial_score=raw_doc.engagement_score
                )

                category = enriched["inferred_category"]
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

                db_doc = RawDocument(
                    source_platform=raw_doc.source_platform,
                    content_text=cleaned_text,
                    content_hash=content_hash,
                    content_language=raw_doc.content_language,
                    source_url=raw_doc.source_url,
                    source_subreddit=raw_doc.source_subreddit,
                    author_id_hash=raw_doc.author_id_hash,
                    engagement_score=enriched["engagement_score"],
                    inferred_category=category,
                    inferred_gender_context=enriched["inferred_gender_context"],
                    inferred_brand_tier=enriched["inferred_brand_tier"],
                    ingestion_run_id=pipeline_run.run_id,
                    source_timestamp=raw_doc.source_timestamp,
                )
                new_db_documents.append(db_doc)

            # 4. Batch Insert
            if new_db_documents:
                db.bulk_save_objects(new_db_documents)
                db.commit()

            stats["total_inserted"] = len(new_db_documents)
            for doc in new_db_documents:
                if doc.source_platform not in stats["by_platform"]:
                    stats["by_platform"][doc.source_platform] = {"fetched": 0, "inserted": 0, "duplicates": 0}
                stats["by_platform"][doc.source_platform]["inserted"] += 1

            # 5. Finalize PipelineRun
            pipeline_run.status = "completed"
            pipeline_run.stats = stats
            pipeline_run.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(pipeline_run)

            logger.info(
                f"Ingestion pipeline completed: {stats['total_inserted']} new documents stored "
                f"({stats['total_duplicates']} duplicates skipped)."
            )

        except Exception as e:
            logger.exception(f"Ingestion pipeline failed: {e}")
            db.rollback()
            pipeline_run.status = "failed"
            stats["errors"].append(str(e))
            pipeline_run.stats = stats
            pipeline_run.completed_at = datetime.now(timezone.utc)
            db.commit()

        finally:
            if should_close_db:
                db.close()

        return pipeline_run


pipeline = IngestionPipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Pulse Multi-Source Ingestion Pipeline")
    parser.add_argument("--sources", type=str, default="playstore,appstore,reddit", help="Comma-separated sources")
    parser.add_argument("--limit", type=int, default=100, help="Document limit per source")
    args = parser.parse_args()

    sources_list = [s.strip() for s in args.sources.split(",") if s.strip()]
    res = pipeline.run(sources=sources_list, limit_per_source=args.limit)
    print("Ingestion run complete:", res.status, res.stats)
