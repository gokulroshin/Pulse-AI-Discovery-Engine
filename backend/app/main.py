import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, corpus, pipeline, extractions, opportunities, evidence, segments, taxonomy
from app.db.base import Base
from app.db.session import engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pulse.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: initial setup and shutdown cleanup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    
    # Ensure database schema is created
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verification/initialization complete.")
    except Exception as e:
        logger.warning(f"Database auto-creation check note: {e}")
        
    yield
    
    logger.info(f"Shutting down {settings.APP_NAME}.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Pulse: Wishlist-to-Purchase Qualitative Discovery & Batch Analytics Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS for seamless public access across Vercel, Railway, and localhost
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [origins]

is_wildcard = "*" in origins or origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else origins,
    allow_origin_regex=r"https://.*" if not is_wildcard else None,
    allow_credentials=False if is_wildcard else True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from app.api.routes import health, corpus, pipeline, extractions, opportunities, evidence, segments, taxonomy, insights

# Register Routers
app.include_router(health.router)
app.include_router(corpus.router)
app.include_router(pipeline.router)
app.include_router(extractions.router)
app.include_router(opportunities.router)
app.include_router(evidence.router)
app.include_router(segments.router)
app.include_router(taxonomy.router)
app.include_router(insights.router)


@app.get("/", tags=["Health & System"])
def root():
    """Root entrypoint returning API service metadata."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }
