"""
Main FastAPI application for Trend Lens backend.

Wires together all components: database, cache, scheduler, and API routes.
Uses the lifespan pattern for startup/shutdown. On startup it creates DB tables,
initializes the Redis cache, and starts the scrape scheduler. On shutdown it
stops the scheduler gracefully.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.config import settings
from app.database import Base, engine
from app.routes import topics, trends
from app import scheduler as app_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan handler for startup and shutdown events.

    Startup:
      1. Create database tables if they don't exist
      2. Initialize fastapi-cache2 with Redis backend
      3. Start the APScheduler scrape job

    Shutdown:
      1. Stop the APScheduler
    """
    # --- Startup ---
    logger.info("Starting Trend Lens API...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Initialize Redis cache
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        FastAPICache.init(RedisBackend(redis_client), prefix="trendlens-cache")
        logger.info("Redis cache initialized at %s", settings.REDIS_URL)
    except Exception as e:
        logger.error("Failed to initialize Redis cache — %s", e)
        logger.warning("API will run without caching")

    # Start scheduler
    app_scheduler.start()
    logger.info("Scheduler started")

    yield

    # --- Shutdown ---
    app_scheduler.stop()
    logger.info("Trend Lens API shut down")


# Create FastAPI app
app = FastAPI(
    title="Trend Lens API",
    version="1.0.0",
    description="Real-time tech trend dashboard API — scrapes Reddit, HN, and GitHub Trending",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trends.router, prefix="/api", tags=["Trends"])
app.include_router(topics.router, prefix="/api", tags=["Topics"])


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint — returns API info and docs link."""
    return {
        "message": "Trend Lens API",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint — verifies database and Redis connectivity.

    Returns status for each dependency and a timestamp.
    """
    health: dict = {
        "status": "ok",
        "db": "unknown",
        "redis": "unknown",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        health["db"] = "ok"
    except Exception as e:
        health["db"] = f"error: {str(e)}"
        health["status"] = "degraded"
        logger.error("Health check: DB failed — %s", e)

    # Check Redis
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health["redis"] = "ok"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"
        logger.error("Health check: Redis failed — %s", e)

    return health


@app.post("/api/trigger-scrape", tags=["Admin"])
async def trigger_scrape() -> dict:
    """
    Manually trigger a scrape + NLP pipeline run.

    Useful for initial data population without waiting for the scheduler.
    """
    import asyncio
    from app.scheduler import scrape_and_save
    from app.cluster import run_full_pipeline
    from app.database import async_session_factory

    logger.info("Manual scrape triggered")

    # Run scrape
    await scrape_and_save()

    # Run NLP pipeline
    async with async_session_factory() as session:
        await run_full_pipeline(session)

    return {"status": "ok", "message": "Scrape and NLP pipeline completed"}
