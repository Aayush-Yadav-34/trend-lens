"""
ORM models for Trend Lens backend.

Defines the Post and Topic tables matching the database schema in AGENTS.md.
Post stores raw scraped data plus NLP-enriched fields (sentiment, topic_id).
Topic stores clustering results — labels, keyword lists, and aggregate stats.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class Topic(Base):
    """NLP-generated topic cluster from KMeans on post titles."""

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(Text, nullable=False)
    post_count = Column(Integer, default=0)
    avg_sentiment = Column(Float, nullable=True)
    top_keywords = Column(ARRAY(Text), nullable=True)
    computed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to posts in this topic cluster
    posts = relationship("Post", back_populates="topic", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, label='{self.label}', post_count={self.post_count})>"


class Post(Base):
    """Raw post scraped from Reddit, Hacker News, or GitHub Trending."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False)
    title = Column(Text, nullable=False)
    score = Column(Integer, default=0)
    url = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    raw_text = Column(Text, nullable=True)
    sentiment = Column(Float, nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)

    # Relationship to topic cluster
    topic = relationship("Topic", back_populates="posts", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, source='{self.source}', title='{self.title[:40]}...')>"

    def to_dict(self) -> dict:
        """Serialize post to dictionary for API responses."""
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "score": self.score,
            "url": self.url,
            "author": self.author,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "raw_text": self.raw_text,
            "sentiment": self.sentiment,
            "topic_id": self.topic_id,
        }


# Indexes for query performance
Index("idx_posts_source", Post.source)
Index("idx_posts_fetched_at", Post.fetched_at.desc())
Index("idx_posts_topic_id", Post.topic_id)
