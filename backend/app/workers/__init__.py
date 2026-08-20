"""Celery Background Workers Package."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "pulse_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.ingestion_tasks",
        "app.workers.extraction_tasks",
        "app.workers.aggregation_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
