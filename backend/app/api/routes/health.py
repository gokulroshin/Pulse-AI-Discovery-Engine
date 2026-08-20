from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.db.session import get_db

router = APIRouter(tags=["Health & System"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    response_model=Dict[str, Any],
)
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns application health, database connectivity status, and system metadata."""
    db_status = "healthy"
    db_error = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "error": db_error,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
