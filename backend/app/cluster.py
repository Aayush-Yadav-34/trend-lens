"""
Clustering module for Trend Lens backend.

Takes NLP-enriched posts and groups them into topic clusters using TF-IDF
vectorization + KMeans. Each cluster gets a human-readable label from its
top TF-IDF keywords. Results are saved to the topics table and posts are
updated with their assigned topic_id. This is the final step of the NLP pipeline.
"""

import logging
from datetime import datetime, timedelta

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import Post, Topic
from app.nlp import process_posts

logger = logging.getLogger(__name__)


def run_clustering(posts: list[dict], n_clusters: int = 8) -> list[dict]:
    """
    Cluster posts by title using TF-IDF + KMeans.

    Uses TfidfVectorizer with max_features=500 and English stop words.
    KMeans with n_clusters = min(n_clusters, len(posts)) to handle small
    datasets. For each cluster, extracts top 5 TF-IDF keywords and creates
    a label from the top 3.

    Returns list of cluster dicts with: cluster_id, label, top_keywords,
    post_indices, avg_sentiment.
    """
    if not posts or len(posts) < 2:
        logger.warning("Clustering: not enough posts (%d) to cluster", len(posts))
        return []

    # Extract titles for vectorization
    titles = [post.get("title", "") for post in posts]

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words="english",
        lowercase=True,
        min_df=1,
        max_df=0.95,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(titles)
    except ValueError as e:
        logger.error("Clustering: TF-IDF failed — %s", e)
        return []

    feature_names = vectorizer.get_feature_names_out()

    # KMeans clustering
    actual_clusters = min(n_clusters, len(posts))
    kmeans = KMeans(
        n_clusters=actual_clusters,
        random_state=42,
        n_init=10,
        max_iter=300,
    )
    cluster_labels = kmeans.fit_predict(tfidf_matrix)

    # Build cluster results
    clusters: list[dict] = []
    for cluster_id in range(actual_clusters):
        # Get post indices for this cluster
        post_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]

        if not post_indices:
            continue

        # Get top 5 TF-IDF keywords from cluster center
        center = kmeans.cluster_centers_[cluster_id]
        top_keyword_indices = np.argsort(center)[::-1][:5]
        top_keywords = [str(feature_names[i]) for i in top_keyword_indices]

        # Label = top 3 keywords joined
        label = " ".join(top_keywords[:3])

        # Average sentiment from posts in cluster
        sentiments = [
            posts[i].get("sentiment", 0.0)
            for i in post_indices
            if posts[i].get("sentiment") is not None
        ]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        clusters.append({
            "cluster_id": cluster_id,
            "label": label,
            "top_keywords": top_keywords,
            "post_indices": post_indices,
            "avg_sentiment": round(avg_sentiment, 4),
            "post_count": len(post_indices),
        })

    logger.info("Clustering: created %d clusters from %d posts", len(clusters), len(posts))
    return clusters


async def save_topics_to_db(
    clusters: list[dict],
    posts: list[dict],
    session: AsyncSession,
) -> None:
    """
    Persist clustering results to the database.

    Inserts each cluster into the topics table, then bulk updates
    posts.topic_id to link posts to their assigned cluster.
    Single commit at end for atomicity.
    """
    if not clusters:
        logger.warning("save_topics_to_db: no clusters to save")
        return

    topic_id_map: dict[int, int] = {}  # cluster_id → topic.id

    for cluster in clusters:
        topic = Topic(
            label=cluster["label"],
            post_count=cluster["post_count"],
            avg_sentiment=cluster["avg_sentiment"],
            top_keywords=cluster["top_keywords"],
            computed_at=datetime.utcnow(),
        )
        session.add(topic)
        await session.flush()  # Get the generated ID
        topic_id_map[cluster["cluster_id"]] = topic.id

    # Bulk update posts with their topic_id
    for cluster in clusters:
        topic_id = topic_id_map[cluster["cluster_id"]]
        post_ids = []
        for idx in cluster["post_indices"]:
            if idx < len(posts) and posts[idx].get("id"):
                post_ids.append(posts[idx]["id"])

        if post_ids:
            await session.execute(
                update(Post).where(Post.id.in_(post_ids)).values(topic_id=topic_id)
            )

    await session.commit()
    logger.info("save_topics_to_db: saved %d topics", len(clusters))


async def run_full_pipeline(session: AsyncSession) -> None:
    """
    End-to-end NLP pipeline: process → cluster → save.

    1. Fetch last 30 min of unprocessed posts from DB (sentiment IS NULL)
    2. Run NLP processing (sentiment + keywords)
    3. Update sentiment scores in DB
    4. Fetch all posts from last 24h for clustering
    5. Run clustering and save topics

    Logs the pipeline completion with post and topic counts.
    """
    logger.info("Pipeline: starting full NLP pipeline")

    # Step 1: Fetch unprocessed posts (sentiment is NULL, last 30 min)
    thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
    result = await session.execute(
        select(Post).where(
            Post.sentiment.is_(None),
            Post.fetched_at >= thirty_min_ago,
        )
    )
    unprocessed = result.scalars().all()

    if unprocessed:
        # Step 2: Process posts through NLP
        post_dicts = [
            {
                "id": p.id,
                "title": p.title,
                "raw_text": p.raw_text or "",
                "source": p.source,
            }
            for p in unprocessed
        ]
        enriched = process_posts(post_dicts)

        # Step 3: Update sentiment in DB
        for post_data in enriched:
            await session.execute(
                update(Post)
                .where(Post.id == post_data["id"])
                .values(sentiment=post_data["sentiment"])
            )
        await session.commit()
        logger.info("Pipeline: updated sentiment for %d posts", len(enriched))
    else:
        logger.info("Pipeline: no unprocessed posts found")

    # Step 4: Fetch all posts from last 24h for clustering
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    result = await session.execute(
        select(Post).where(Post.fetched_at >= twenty_four_hours_ago)
    )
    all_recent = result.scalars().all()

    if len(all_recent) < 2:
        logger.warning("Pipeline: not enough recent posts (%d) to cluster", len(all_recent))
        return

    # Convert to dicts for clustering
    post_dicts = [
        {
            "id": p.id,
            "title": p.title,
            "raw_text": p.raw_text or "",
            "source": p.source,
            "sentiment": p.sentiment or 0.0,
        }
        for p in all_recent
    ]

    # Step 5: Run clustering and save
    from app.config import settings
    clusters = run_clustering(post_dicts, n_clusters=settings.N_CLUSTERS)

    if clusters:
        await save_topics_to_db(clusters, post_dicts, session)

    logger.info(
        "Pipeline complete — %d posts, %d topics",
        len(all_recent),
        len(clusters),
    )


if __name__ == "__main__":
    # Test with 10 sample post dicts
    logging.basicConfig(level=logging.INFO)

    sample_posts = [
        {"title": "Rust async runtime performance benchmarks", "sentiment": 0.5},
        {"title": "Python type hints best practices guide", "sentiment": 0.3},
        {"title": "React server components deep dive tutorial", "sentiment": 0.6},
        {"title": "Kubernetes deployment strategies explained", "sentiment": 0.1},
        {"title": "WebAssembly runtime for edge computing", "sentiment": 0.4},
        {"title": "Machine learning model optimization techniques", "sentiment": 0.2},
        {"title": "Go concurrency patterns and goroutines", "sentiment": 0.5},
        {"title": "TypeScript 5.0 new features overview", "sentiment": 0.7},
        {"title": "Docker container security best practices", "sentiment": -0.1},
        {"title": "PostgreSQL performance tuning and indexing", "sentiment": 0.3},
    ]

    clusters = run_clustering(sample_posts, n_clusters=4)
    for cluster in clusters:
        print(f"\n--- Cluster {cluster['cluster_id']} ---")
        print(f"  Label:         {cluster['label']}")
        print(f"  Top Keywords:  {cluster['top_keywords']}")
        print(f"  Post Count:    {cluster['post_count']}")
        print(f"  Avg Sentiment: {cluster['avg_sentiment']}")
        print(f"  Post Indices:  {cluster['post_indices']}")
