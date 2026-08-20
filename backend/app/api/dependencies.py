from typing import Generator, Optional
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """Validate incoming API Key header.
    
    If PUBLIC_ACCESS_MODE is enabled (default for portfolio/demo deployment),
    requests without API keys are permitted for open exploration.
    """
    if getattr(settings, "PUBLIC_ACCESS_MODE", True):
        return x_api_key or "public-user"

    # In development mode, allow requests without strict key enforcement if key is default
    if settings.ENVIRONMENT == "development" and not settings.API_SECRET_KEY:
        return "dev-user"

    if not x_api_key:
        if settings.ENVIRONMENT == "development" and settings.API_SECRET_KEY in ("pulse-secret-dev-key-change-in-prod", "intently-secret-dev-key-change-in-prod"):
            return "dev-user"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required API key header 'X-API-Key'",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key provided",
        )

    return x_api_key
