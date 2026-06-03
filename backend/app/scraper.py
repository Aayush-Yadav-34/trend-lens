"""
Scraper module for Trend Lens backend.

Contains async functions to fetch posts from Reddit (via PRAW), Hacker News
(via Firebase REST API), and GitHub Trending (via HTML scraping). Each source
has its own fetcher wrapped in try/except so one failing source never crashes
the pipeline. fetch_all() orchestrates all three and returns combined results.
"""

import asyncio
import logging
from datetime import datetime

import httpx
import praw
import requests
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

# Reddit subreddits to scrape
SUBREDDITS = [
    "programming",
    "webdev",
    "MachineLearning",
    "Python",
    "javascript",
    "devops",
    "golang",
    "rust",
]

# Hacker News Firebase API endpoints
HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"

# GitHub Trending page URL
GITHUB_TRENDING_URL = "https://github.com/trending?since=daily&spoken_language_code=en"


async def fetch_reddit() -> list[dict]:
    """
    Fetch top 25 hot posts from each configured subreddit using PRAW.

    PRAW is synchronous, so we run it in a thread executor to avoid blocking
    the async event loop. Returns a list of post dicts.
    """
    posts: list[dict] = []

    def _fetch_sync() -> list[dict]:
        """Synchronous PRAW fetch — runs in executor."""
        results: list[dict] = []
        try:
            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
            reddit.read_only = True

            for subreddit_name in SUBREDDITS:
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    for submission in subreddit.hot(limit=25):
                        results.append({
                            "source": "reddit",
                            "title": submission.title,
                            "score": submission.score,
                            "url": f"https://reddit.com{submission.permalink}",
                            "author": str(submission.author) if submission.author else "unknown",
                            "raw_text": submission.selftext or "",
                            "fetched_at": datetime.utcnow(),
                        })
                    logger.info("Reddit: fetched %d posts from r/%s", len(results), subreddit_name)
                except Exception as e:
                    logger.error("Reddit: failed to fetch r/%s — %s", subreddit_name, e)
                    continue
        except Exception as e:
            logger.error("Reddit: failed to initialize PRAW — %s", e)
        return results

    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(None, _fetch_sync)
    logger.info("Reddit: total %d posts fetched", len(posts))
    return posts


async def fetch_hn() -> list[dict]:
    """
    Fetch top 100 stories from Hacker News Firebase API.

    Fetches story IDs first, then concurrently fetches each story detail
    using asyncio.gather. Filters out non-story items.
    """
    posts: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch top story IDs
            response = await client.get(HN_TOP_STORIES_URL)
            response.raise_for_status()
            story_ids: list[int] = response.json()[:100]
            logger.info("HN: fetched %d story IDs", len(story_ids))

            # Fetch each story concurrently
            async def _fetch_story(story_id: int) -> dict | None:
                try:
                    url = HN_ITEM_URL.format(item_id=story_id)
                    resp = await client.get(url)
                    resp.raise_for_status()
                    item = resp.json()
                    if item and item.get("type") == "story":
                        return {
                            "source": "hn",
                            "title": item.get("title", ""),
                            "score": item.get("score", 0),
                            "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                            "author": item.get("by", "unknown"),
                            "raw_text": item.get("text", ""),
                            "fetched_at": datetime.utcnow(),
                        }
                except Exception as e:
                    logger.error("HN: failed to fetch story %d — %s", story_id, e)
                return None

            results = await asyncio.gather(*[_fetch_story(sid) for sid in story_ids])
            posts = [p for p in results if p is not None]
            logger.info("HN: total %d posts fetched", len(posts))

    except Exception as e:
        logger.error("HN: failed to fetch top stories — %s", e)

    return posts


async def fetch_github() -> list[dict]:
    """
    Scrape GitHub Trending page for daily trending repositories.

    Uses requests + BeautifulSoup4 (synchronous) in an executor to avoid
    blocking the async loop. Extracts repo name, description, and star count.
    """
    posts: list[dict] = []

    def _fetch_sync() -> list[dict]:
        """Synchronous GitHub scraping — runs in executor."""
        results: list[dict] = []
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            }
            response = requests.get(GITHUB_TRENDING_URL, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            repo_articles = soup.select("article.Box-row")

            for article in repo_articles[:30]:
                # Extract repo name (owner/repo)
                title_tag = article.select_one("h2 a")
                if not title_tag:
                    continue
                repo_name = title_tag.get_text(strip=True).replace("\n", "").replace(" ", "")

                # Extract description
                desc_tag = article.select_one("p")
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                # Extract stars count
                stars_text = ""
                star_links = article.select("a.Link--muted")
                for link in star_links:
                    svg = link.select_one("svg.octicon-star")
                    if svg:
                        stars_text = link.get_text(strip=True).replace(",", "")
                        break

                try:
                    stars = int(stars_text) if stars_text else 0
                except ValueError:
                    stars = 0

                repo_url = f"https://github.com/{repo_name}"
                results.append({
                    "source": "github",
                    "title": repo_name,
                    "score": stars,
                    "url": repo_url,
                    "author": repo_name.split("/")[0] if "/" in repo_name else "unknown",
                    "raw_text": description,
                    "fetched_at": datetime.utcnow(),
                })

            logger.info("GitHub: fetched %d trending repos", len(results))
        except Exception as e:
            logger.error("GitHub: failed to scrape trending page — %s", e)
        return results

    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(None, _fetch_sync)
    logger.info("GitHub: total %d posts fetched", len(posts))
    return posts


async def fetch_all() -> list[dict]:
    """
    Fetch posts from all sources, combining results.

    Each source is wrapped in try/except so one failing source never
    crashes the others. Returns the combined list of all posts.
    """
    all_posts: list[dict] = []

    # Reddit
    try:
        reddit_posts = await fetch_reddit()
        all_posts.extend(reddit_posts)
        logger.info("fetch_all: Reddit returned %d posts", len(reddit_posts))
    except Exception as e:
        logger.error("fetch_all: Reddit failed — %s", e)

    # Hacker News
    try:
        hn_posts = await fetch_hn()
        all_posts.extend(hn_posts)
        logger.info("fetch_all: HN returned %d posts", len(hn_posts))
    except Exception as e:
        logger.error("fetch_all: HN failed — %s", e)

    # GitHub Trending
    try:
        github_posts = await fetch_github()
        all_posts.extend(github_posts)
        logger.info("fetch_all: GitHub returned %d posts", len(github_posts))
    except Exception as e:
        logger.error("fetch_all: GitHub failed — %s", e)

    logger.info("fetch_all: total %d posts from all sources", len(all_posts))
    return all_posts
