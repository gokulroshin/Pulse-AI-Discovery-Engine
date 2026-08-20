import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db, SessionLocal
from app.api.dependencies import verify_api_key
from app.models.pipeline_run import PipelineRun
from app.ingestion.pipeline import pipeline
from app.extraction.batch_processor import batch_processor

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline Engine"])


class PipelineRunRequest(BaseModel):
    stage: str = Field(
        default="ingestion",
        description="Pipeline stage to trigger: ingestion | extraction | clustering | scoring | full_pipeline"
    )
    sources: Optional[List[str]] = Field(
        default=["playstore", "appstore", "reddit"],
        description="Data sources to scrape (for ingestion stage)"
    )
    limit_per_source: int = Field(
        default=200,
        ge=10,
        le=2000,
        description="Maximum documents to fetch per source"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Limit number of documents to process in extraction stage"
    )
    batch_size: Optional[int] = Field(
        default=20,
        description="Batch size per LLM request"
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional configuration options"
    )


def execute_ingestion_in_background(run_id: str, sources: List[str], limit: int, config: Dict[str, Any]):
    """Background worker function executing ingestion pipeline without blocking API response."""
    db = SessionLocal()
    try:
        pipeline.run(
            sources=sources,
            limit_per_source=limit,
            db=db,
            config=config,
            run_id=run_id,
        )
    finally:
        db.close()


from app.aggregation.coordinator import aggregation_coordinator


def execute_extraction_in_background(run_id: str, limit: Optional[int], batch_size: int, config: Dict[str, Any]):
    """Background worker function executing extraction pipeline without blocking API response."""
    db = SessionLocal()
    try:
        batch_processor.run(
            limit=limit,
            batch_size=batch_size,
            filter_platform=config.get("filter_platform"),
            filter_category=config.get("filter_category"),
            db=db,
        )
    finally:
        db.close()


def execute_aggregation_in_background(run_id: str, target_k: Optional[int], config: Dict[str, Any]):
    """Background worker function executing clustering & scoring pipeline."""
    db = SessionLocal()
    try:
        aggregation_coordinator.run(
            db=db,
            run_id=run_id,
            target_k=target_k,
        )
    finally:
        db.close()


def execute_full_pipeline_in_background(
    run_id: str,
    sources: List[str],
    limit_per_source: int,
    limit: Optional[int],
    batch_size: int,
    config: Dict[str, Any]
):
    """Executes the complete end-to-end pipeline: Ingestion -> Extraction -> Aggregation & Scoring."""
    db = SessionLocal()
    try:
        # Step 1: Ingestion
        pipeline.run(
            sources=sources,
            limit_per_source=limit_per_source,
            db=db,
            config=config,
            run_id=run_id,
        )
        # Step 2: Extraction
        batch_processor.run(
            limit=limit,
            batch_size=batch_size,
            filter_platform=config.get("filter_platform"),
            filter_category=config.get("filter_category"),
            db=db,
        )
        # Step 3: Aggregation & Scoring
        aggregation_coordinator.run(
            db=db,
            run_id=run_id,
            target_k=config.get("target_k"),
        )
    finally:
        db.close()


@router.post("/run", summary="Trigger Pipeline Stage Execution")
def trigger_pipeline_run(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Trigger an asynchronous execution of a pipeline stage."""
    run = PipelineRun(
        stage=request.stage,
        status="pending",
        config={
            "sources": request.sources,
            "limit_per_source": request.limit_per_source,
            "limit": request.limit,
            "batch_size": request.batch_size,
            **request.config,
        },
        stats={},
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    stage_lower = request.stage.lower()

    if stage_lower == "ingestion":
        background_tasks.add_task(
            execute_ingestion_in_background,
            run.run_id,
            request.sources or ["playstore", "appstore", "reddit"],
            request.limit_per_source,
            request.config or {},
        )
    elif stage_lower == "extraction":
        background_tasks.add_task(
            execute_extraction_in_background,
            run.run_id,
            request.limit,
            request.batch_size or 20,
            request.config or {},
        )
    elif stage_lower in ("clustering", "scoring", "aggregation"):
        background_tasks.add_task(
            execute_aggregation_in_background,
            run.run_id,
            request.config.get("target_k") if request.config else None,
            request.config or {},
        )
    elif stage_lower in ("full", "full_pipeline"):
        background_tasks.add_task(
            execute_full_pipeline_in_background,
            run.run_id,
            request.sources or ["playstore", "appstore", "reddit"],
            request.limit_per_source,
            request.limit,
            request.batch_size or 20,
            request.config or {},
        )
    else:
        run.status = "completed"
        run.stats = {"message": f"Stage {request.stage} scheduled"}
        db.commit()

    return {
        "run_id": run.run_id,
        "stage": run.stage,
        "status": run.status,
        "started_at": run.started_at.isoformat(),
    }


@router.get("/status", summary="Get Pipeline Runs History")
def get_pipeline_runs(
    limit: int = 10,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """List recent pipeline execution runs."""
    runs = (
        db.query(PipelineRun)
        .order_by(desc(PipelineRun.started_at))
        .limit(limit)
        .all()
    )

    return {
        "runs": [
            {
                "run_id": r.run_id,
                "stage": r.stage,
                "status": r.status,
                "config": r.config,
                "stats": r.stats,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]
    }


@router.get("/status/{run_id}", summary="Get Single Pipeline Run Status")
def get_pipeline_run_by_id(
    run_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Retrieve detailed status and stats for a specific pipeline run."""
    run = db.query(PipelineRun).filter_by(run_id=run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run '{run_id}' not found",
        )

    return {
        "run_id": run.run_id,
        "stage": run.stage,
        "status": run.status,
        "config": run.config,
        "stats": run.stats,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
