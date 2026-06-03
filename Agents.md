# Trend Lens — AGENTS.md

## What this project is
Trend Lens is a real-time tech trend dashboard that scrapes Reddit, Hacker News,
and GitHub Trending, runs an NLP pipeline on the posts, and displays an interactive
visualization of what's trending in tech. Built to demonstrate full-stack Python +
React skills with a real NLP pipeline end-to-end.

---

## Tech stack

### Backend
- Language: Python 3.11+
- Framework: FastAPI (async, not Flask)
- Scheduler: APScheduler (runs inside FastAPI process)
- NLP: spaCy (en_core_web_sm), vaderSentiment
- ML: scikit-learn (TfidfVectorizer + KMeans, n_clusters=8)
- ORM: SQLAlchemy (async) with asyncpg driver
- Cache: fastapi-cache2 with Redis backend (15 min TTL on NLP results)
- HTTP client: httpx (async) for API calls
- HTML scraping: requests + BeautifulSoup4

### Frontend
- Scaffold: Vite + React 18
- Charts: Recharts (line/bar charts), D3.js (bubble chart)
- Data fetching: SWR (5 min revalidation interval)
- Styling: Tailwind CSS
- Routing: React Router v6

### Databases
- PostgreSQL 15 (primary store — posts + topics)
- Redis 7 (API response cache)

### DevOps
- Docker + docker-compose (wires backend, PostgreSQL, Redis)
- Backend deploys to Railway or Render
- Frontend deploys to Vercel

---

## Data sources (all free, no paid APIs)

| Source | Method | Library |
|---|---|---|
| Reddit | PRAW (read-only OAuth) | praw |
| Hacker News | Firebase public REST API | httpx |
| GitHub Trending | HTML scrape | requests + BeautifulSoup4 |

### Reddit subreddits to scrape
r/programming, r/webdev, r/MachineLearning, r/Python,
r/javascript, r/devops, r/golang, r/rust

### HN endpoint
https://hacker-news.firebaseio.com/v0/topstories.json
Then fetch each story: https://hacker-news.firebaseio.com/v0/item/{id}.json

### GitHub Trending URL
https://github.com/trending?since=daily&spoken_language_code=en

---

## Database schema

```sql
-- Raw posts from all sources
CREATE TABLE posts (
  id          SERIAL PRIMARY KEY,
  source      VARCHAR(20) NOT NULL,   -- 'reddit', 'hn', 'github'
  title       TEXT NOT NULL,
  score       INT DEFAULT 0,
  url         TEXT,
  author      VARCHAR(100),
  fetched_at  TIMESTAMP DEFAULT NOW(),
  raw_text    TEXT,
  sentiment   FLOAT,                  -- VADER compound score (-1 to +1)
  topic_id    INT REFERENCES topics(id)
);

-- NLP-generated topic clusters
CREATE TABLE topics (
  id            SERIAL PRIMARY KEY,
  label         TEXT NOT NULL,         -- top keywords joined: "rust async wasm"
  post_count    INT DEFAULT 0,
  avg_sentiment FLOAT,
  top_keywords  TEXT[],
  computed_at   TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_posts_source ON posts(source);
CREATE INDEX idx_posts_fetched_at ON posts(fetched_at DESC);
CREATE INDEX idx_posts_topic_id ON posts(topic_id);
```

---

## Folder structure
trend-lens/
├── AGENTS.md                    ← you are here
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI app, lifespan, CORS, cache init
│       ├── config.py            # Settings via pydantic-settings + .env
│       ├── database.py          # Async SQLAlchemy engine + session
│       ├── models.py            # SQLAlchemy ORM models (Post, Topic)
│       ├── scraper.py           # Reddit + HN + GitHub fetchers
│       ├── scheduler.py         # APScheduler job definitions
│       ├── nlp.py               # Text cleaning + spaCy + VADER
│       ├── cluster.py           # TF-IDF + KMeans + topic labeling
│       └── routes/
│           ├── init.py
│           ├── trends.py        # GET /api/trends
│           └── topics.py        # GET /api/topics, GET /api/topics/{id}/posts
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── hooks/
│       │   └── useTrends.js     # SWR fetchers
│       ├── components/
│       │   ├── TrendChart.jsx   # Recharts — post volume over time
│       │   ├── TopicBubble.jsx  # D3 bubble — size=count, color=sentiment
│       │   ├── SentimentBar.jsx # Recharts bar — sentiment breakdown
│       │   ├── TrendCard.jsx    # Individual post card with source badge
│       │   └── FilterBar.jsx    # Source + time range filters
│       └── pages/
│           ├── Dashboard.jsx    # Main view
│           └── TopicDetail.jsx  # Drill into a single topic cluster

---

## API endpoints
GET  /api/trends
?source=reddit|hn|github|all   (default: all)
?hours=6|24|48|168             (default: 24)
?limit=50                      (default: 50)
Returns: list of posts sorted by score desc
GET  /api/topics
?hours=24                      (default: 24)
Returns: all topic clusters with post_count + avg_sentiment + top_keywords
GET  /api/topics/{id}/posts
?limit=20                      (default: 20)
Returns: posts belonging to topic {id}
GET  /api/health
Returns: { status: "ok", db: "ok", redis: "ok" }

---

## NLP pipeline (runs every 30 min via APScheduler)
Step 1 — Scrape
Reddit (top 25 posts/subreddit) + HN (top 100) + GitHub Trending (top 30)
→ save raw posts to PostgreSQL
Step 2 — Clean (nlp.py: clean_text)
Strip URLs, HTML tags, special characters, lowercase
Step 3 — Keyword extraction (nlp.py: extract_keywords)
spaCy noun chunks on cleaned title + raw_text
Filter: remove stopwords, keep chunks with 1-3 words
Step 4 — Sentiment (nlp.py: score_sentiment)
VADER compound score on post title
Save to posts.sentiment column
Step 5 — Clustering (cluster.py: run_clustering)
TfidfVectorizer on all post titles from last 24h
KMeans(n_clusters=8) → assign each post a cluster label
Label each cluster by joining its top 3 TF-IDF keywords
Save clusters to topics table, update posts.topic_id
Step 6 — Cache invalidation
Clear Redis cache after clustering completes
Next API request recomputes from fresh DB data and re-caches

---

## Environment variables

All env vars must be read via `pydantic-settings` in `config.py`. Never hardcode.

```bash
# .env.example

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/trendlens

# Redis
REDIS_URL=redis://localhost:6379

# Reddit API (get from reddit.com/prefs/apps — create a "script" app)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=TrendLens/1.0 by YourUsername

# App
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
CACHE_TTL_SECONDS=900
SCRAPE_INTERVAL_MINUTES=30
N_CLUSTERS=8
```

---

## Docker setup

```yaml
# docker-compose.yml structure (agent should write the full file)
services:
  db:        PostgreSQL 15, port 5432, volume for persistence
  redis:     Redis 7 alpine, port 6379
  backend:   Build from backend/Dockerfile, depends_on db + redis,
             port 8000, mounts .env
  # Frontend deploys separately to Vercel — not in docker-compose
```

---

## Code quality rules (all agents must follow)

- Python 3.11+ type hints on every function signature
- Every async route must use async def and await — no sync blocking calls
- All env vars via pydantic-settings Config class, never os.environ directly
- Every API route: try/except with HTTPException and proper status codes
- Every scraper function: try/except per source — one source failing must not
  crash the others
- Logging: use Python logging module (not print), log at INFO for normal flow,
  ERROR for exceptions
- Frontend components must handle three states: loading skeleton, error message,
  data loaded
- SWR fetcher must include error boundary
- No hardcoded URLs in frontend — use VITE_API_URL env var

---

## Agent instructions

- Always write COMPLETE files — no TODOs, no placeholders, no "add logic here"
- After writing a file, run it to confirm zero import errors before finishing
- Run pip install / npm install before writing any import for a new package
- If you discover a schema or API mismatch with another module, fix it and note
  the change clearly so the integration agent can review
- Prefer simple working code over clever code — this is a portfolio project,
  readability matters
- Add a one-paragraph docstring at the top of every Python file explaining
  what it does and how it fits into the pipeline