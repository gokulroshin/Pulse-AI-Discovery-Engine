"""Celery background worker tasks for LLM reason extraction."""

import logging
from typing import Optional, Dict, Any
from app.workers import celery_app
from app.extraction.batch_processor import batch_processor

logger = logging.getLogger("pulse.workers.extraction")


@celery_app.task(bind=True, name="tasks.run_extraction_pipeline")
def run_extraction_task(
    self,
    limit: Optional[int] = None,
    batch_size: Optional[int] = None,
    filter_platform: Optional[str] = None,
    filter_category: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery background task wrapper for ExtractionBatchProcessor."""
    logger.info(f"Starting Celery extraction task {self.request.id} (limit={limit}, batch_size={batch_size})")
    result = batch_processor.run(
        limit=limit,
        batch_size=batch_size,
        filter_platform=filter_platform,
        filter_category=filter_category,
    )
    return {
        "run_id": result.run_id,
        "stage": result.stage,
        "status": result.status,
        "stats": result.stats,
    }
