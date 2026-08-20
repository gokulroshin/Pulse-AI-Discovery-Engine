"""Celery background worker tasks for Layer 3 & Layer 4 Aggregation and Opportunity Scoring."""

import logging
from typing import Dict, Any, Optional
from app.workers import celery_app
from app.aggregation.coordinator import aggregation_coordinator

logger = logging.getLogger("pulse.workers.aggregation")


@celery_app.task(bind=True, name="tasks.run_aggregation_pipeline")
def run_aggregation_pipeline(
    self,
    run_id: Optional[str] = None,
    target_k: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Background Celery task to execute clustering, taxonomy construction, and scoring."""
    logger.info(f"Starting Celery aggregation task {self.request.id} (Pipeline Run: {run_id})...")
    try:
        result = aggregation_coordinator.run(
            run_id=run_id,
            target_k=target_k,
        )
        logger.info(f"Celery aggregation task {self.request.id} completed successfully.")
        return result
    except Exception as exc:
        logger.error(f"Celery aggregation task {self.request.id} failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30, max_retries=2)
