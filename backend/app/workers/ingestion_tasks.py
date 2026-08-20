import logging
from typing import List, Optional, Dict, Any
from app.workers import celery_app
from app.ingestion.pipeline import pipeline

logger = logging.getLogger("pulse.workers.ingestion")


@celery_app.task(bind=True, name="tasks.run_ingestion_pipeline")
def run_ingestion_task(
    self,
    sources: Optional[List[str]] = None,
    limit_per_source: int = 200,
    config: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery background task wrapper for IngestionPipeline execution."""
    logger.info(f"Starting Celery ingestion task {self.request.id} for sources: {sources}")
    result = pipeline.run(
        sources=sources,
        limit_per_source=limit_per_source,
        config=config,
        run_id=run_id,
    )
    return {
        "run_id": result.run_id,
        "status": result.status,
        "stats": result.stats,
    }
