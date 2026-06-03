"""
Trends API route for Trend Lens backend.

Provides GET /api/trends endpoint that returns posts from all scraped sources
(Reddit, HN, GitHub) filtered by source, time range, and count limit.
Results are sorted by score descending and cached for 5 minutes.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Post

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/trends")
@cache(expire=300)
async def get_trends(
    source: str = Query(default="all", description="Filter by source: reddit, hn, github, or all"),
    hours: int = Query(default=24, description="Time range in hours: 6, 24, 48, or 168"),
    limit: int = Query(default=50, ge=1, le=200, description="Number of posts to return"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Get trending posts sorted by score, optionally filtered by source and time range.

    Returns a list of post dicts with: id, source, title, score, url, author,
    fetched_at, sentiment, topic_id.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        query = select(Post).where(Post.fetched_at >= cutoff)

        if source != "all":
            valid_sources = {"reddit", "hn", "github"}
            if source not in valid_sources:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid source '{source}'. Must be one of: {', '.join(valid_sources)}",
                )
            query = query.where(Post.source == source)

        query = query.order_by(Post.score.desc()).limit(limit)

        result = await db.execute(query)
        posts = result.scalars().all()

        return [post.to_dict() for post in posts]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("GET /api/trends failed — %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch trends") from e
