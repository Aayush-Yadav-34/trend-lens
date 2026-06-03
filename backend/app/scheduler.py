"""
Scheduler module for Trend Lens backend.

Uses APScheduler's AsyncIOScheduler to run the data scraping and NLP pipeline
on a configurable interval (default: every 30 minutes). The scheduler runs
inside the FastAPI process — start() and stop() are called from the app lifespan.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models import Post
from app.scraper import fetch_all

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scrape_and_save() -> None:
    """
    Fetch posts from all sources and save to PostgreSQL.

    Skips duplicate posts by checking if a URL already exists in the database.
    This is the main job that runs on the configured interval.
    """
    logger.info("Scheduler: starting scrape job at %s", datetime.utcnow().isoformat())

    try:
        # Fetch from all sources
        posts = await fetch_all()
        if not posts:
            logger.warning("Scheduler: no posts fetched from any source")
            return

        # Save to database, skipping duplicates by URL
        async with async_session_factory() as session:
            saved_count = 0
            skipped_count = 0

            for post_data in posts:
                # Check for duplicate URL
                if post_data.get("url"):
                    existing = await session.execute(
                        select(Post).where(Post.url == post_data["url"])
                    )
                    if existing.scalar_one_or_none() is not None:
                        skipped_count += 1
                        continue

                # Create new post
                post = Post(
                    source=post_data["source"],
                    title=post_data["title"],
                    score=post_data.get("score", 0),
                    url=post_data.get("url"),
                    author=post_data.get("author"),
                    raw_text=post_data.get("raw_text", ""),
                    fetched_at=post_data.get("fetched_at", datetime.utcnow()),
                )
                session.add(post)
                saved_count += 1

            await session.commit()
            logger.info(
                "Scheduler: saved %d new posts, skipped %d duplicates",
                saved_count,
                skipped_count,
            )

    except Exception as e:
        logger.error("Scheduler: scrape_and_save failed — %s", e)


def start() -> None:
    """Start the APScheduler with the scrape job on the configured interval."""
    scheduler.add_job(
        scrape_and_save,
        "interval",
        minutes=settings.SCRAPE_INTERVAL_MINUTES,
        id="scrape_job",
        name="Scrape all sources",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(
        "Scheduler: started — scraping every %d minutes",
        settings.SCRAPE_INTERVAL_MINUTES,
    )


def stop() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler: stopped")
