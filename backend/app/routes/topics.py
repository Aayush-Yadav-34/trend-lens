"""
Topics API routes for Trend Lens backend.

Provides two endpoints:
  GET /api/topics — returns all topic clusters with post_count, avg_sentiment,
    and top_keywords, ordered by post_count descending. Cached for 15 minutes.
  GET /api/topics/{topic_id}/posts — returns posts belonging to a specific topic
    cluster, ordered by score descending. Cached for 5 minutes. 404 if topic not found.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Post, Topic

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/topics")
@cache(expire=900)
async def get_topics(
    hours: int = Query(default=24, description="Time range in hours"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Get topic clusters from the most recent NLP pipeline run within the specified timeframe.

    Returns list of topic dicts with: id, label, post_count, avg_sentiment,
    top_keywords, computed_at.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Get the latest computed_at timestamp within the cutoff
        latest_ts_result = await db.execute(
            select(Topic.computed_at)
            .where(Topic.computed_at >= cutoff)
            .order_by(Topic.computed_at.desc())
            .limit(1)
        )
        latest_ts = latest_ts_result.scalar_one_or_none()

        if not latest_ts:
            return []

        # Return topics from the latest run (within a 10-second window to be safe)
        result = await db.execute(
            select(Topic)
            .where(
                Topic.computed_at >= latest_ts - timedelta(seconds=10),
                Topic.computed_at <= latest_ts + timedelta(seconds=10),
            )
            .order_by(Topic.post_count.desc())
        )
        topics = result.scalars().all()

        return [
            {
                "id": topic.id,
                "label": topic.label,
                "post_count": topic.post_count,
                "avg_sentiment": topic.avg_sentiment,
                "top_keywords": topic.top_keywords,
                "computed_at": topic.computed_at.isoformat() if topic.computed_at else None,
            }
            for topic in topics
        ]

    except Exception as e:
        logger.error("GET /api/topics failed — %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch topics") from e


@router.get("/topics/{topic_id}/posts")
@cache(expire=300)
async def get_topic_posts(
    topic_id: int,
    limit: int = Query(default=20, ge=1, le=100, description="Number of posts to return"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Get posts belonging to a specific topic cluster, ordered by score descending.

    Returns 404 if the topic does not exist.
    """
    try:
        # Check topic exists
        topic_result = await db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = topic_result.scalar_one_or_none()

        if topic is None:
            raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")

        # Fetch posts for this topic
        result = await db.execute(
            select(Post)
            .where(Post.topic_id == topic_id)
            .order_by(Post.score.desc())
            .limit(limit)
        )
        posts = result.scalars().all()

        return [post.to_dict() for post in posts]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("GET /api/topics/%d/posts failed — %s", topic_id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch topic posts") from e
