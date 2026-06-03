You are building Trend Lens from scratch — a real-time tech trend dashboard.
Read AGENTS.md in the project root before writing anything. Follow every
rule in it exactly throughout this entire session.

You will build the project sequentially in this exact order. Do not skip
ahead. Complete each step fully before moving to the next.

---

PHASE 1 — Project foundation

Step 1: Write backend/requirements.txt
Include pinned versions for: fastapi, uvicorn[standard], sqlalchemy[asyncio],
asyncpg, alembic, praw, httpx, beautifulsoup4, requests, apscheduler,
pydantic-settings, python-dotenv, spacy, vaderSentiment, scikit-learn,
fastapi-cache2[redis], redis, aioredis

Step 2: Write backend/app/config.py
pydantic-settings Settings class that reads every env var listed in AGENTS.md.
Include sensible defaults where safe (CACHE_TTL_SECONDS=900,
SCRAPE_INTERVAL_MINUTES=30, N_CLUSTERS=8, ENVIRONMENT=development).

Step 3: Write backend/app/database.py
Async SQLAlchemy engine using asyncpg. Async session factory. get_db()
FastAPI dependency. Base declarative class that models.py will import.

Step 4: Write backend/app/models.py
SQLAlchemy ORM models for Post and Topic matching the schema in AGENTS.md
exactly. Import Base from database.py.

After Step 4: run this check:
  pip install -r backend/requirements.txt
  python -c "from app.models import Post, Topic; print('models ok')"
Fix any errors before continuing.

---

PHASE 2 — Data pipeline

Step 5: Write backend/app/scraper.py
Three async functions:
  fetch_reddit() — PRAW, subreddits from AGENTS.md, top 25 posts each,
    hot sort. Return list of dicts with keys:
    source, title, score, url, author, raw_text
  fetch_hn() — httpx, top 100 story IDs from Firebase API, fetch each
    story concurrently with asyncio.gather, filter type != 'story'.
    score = item.score, raw_text = item.text or ""
  fetch_github() — requests + BeautifulSoup4, scrape
    https://github.com/trending?since=daily, extract repo name (title),
    description (raw_text), stars as score
  fetch_all() — calls all three wrapped in individual try/except so one
    failing source never crashes the others. Combines and returns all results.

Step 6: Write backend/app/scheduler.py
APScheduler AsyncIOScheduler. One job: calls fetch_all() then saves results
to PostgreSQL via async session, skipping duplicate URLs. Runs every
SCRAPE_INTERVAL_MINUTES. Expose start() and stop() functions for main.py
lifespan to call.

After Step 6: run:
  python -c "from app.scraper import fetch_all; print('scraper ok')"
  python -c "from app.scheduler import start, stop; print('scheduler ok')"
Fix any errors before continuing.

---

PHASE 3 — NLP pipeline

Step 7: Write backend/app/nlp.py
Four functions:
  clean_text(text: str) -> str
    Lowercase, strip URLs (regex), strip HTML (regex), strip special chars,
    strip extra whitespace.

  extract_keywords(text: str, nlp_model) -> list[str]
    spaCy noun chunks on cleaned text, filter stopwords and
    chunks shorter than 2 chars, return lowercase stripped list.

  score_sentiment(text: str, analyzer) -> float
    VADER compound score on raw text (not cleaned — VADER works better
    on natural text with punctuation).

  process_posts(posts: list[dict]) -> list[dict]
    Load spaCy (en_core_web_sm) and VADER once. Enrich each post dict
    with sentiment (float) and keywords (list[str]). Return enriched list.

Add a __main__ block at the bottom that tests all functions with 3 sample
titles and prints results clearly.

Step 8: Write backend/app/cluster.py
Three functions:
  run_clustering(posts: list[dict], n_clusters: int = 8) -> list[dict]
    TfidfVectorizer(max_features=500, stop_words='english') on titles.
    KMeans(n_clusters=min(n_clusters, len(posts)), random_state=42, n_init=10).
    For each cluster: get top 5 TF-IDF keywords from cluster center.
    Label = top 3 keywords joined by space.
    Return list of: { cluster_id, label, top_keywords, post_indices,
    avg_sentiment }

  save_topics_to_db(clusters, posts, session) -> None
    Insert each cluster into topics table, then bulk update posts.topic_id.
    Single commit at end. Log topics saved.

  run_full_pipeline(session) -> None
    Fetch last 30 min of unprocessed posts from DB.
    Call process_posts(), update sentiment in DB.
    Fetch all posts from last 24h for clustering.
    Call run_clustering() then save_topics_to_db().
    Log: "Pipeline complete — N posts, M topics"

Add a __main__ block that runs the full pipeline on 10 sample post dicts
and prints resulting topic labels.

After Step 8: run:
  python -m spacy download en_core_web_sm
  python backend/app/nlp.py
  python backend/app/cluster.py
Fix any errors before continuing.

---

PHASE 4 — FastAPI backend

Step 9: Write backend/app/routes/__init__.py
Empty file — package marker only.

Step 10: Write backend/app/routes/trends.py
GET /api/trends
  Query params: source (default "all"), hours (default 24), limit (default 50)
  Filter posts by fetched_at and source, order by score DESC.
  Cache with @cache(expire=300).
  Return list of post dicts: id, source, title, score, url, author,
  fetched_at, sentiment, topic_id

Step 11: Write backend/app/routes/topics.py
GET /api/topics
  Query params: hours (default 24)
  Return all topics ordered by post_count DESC.
  Cache with @cache(expire=900).

GET /api/topics/{topic_id}/posts
  Query params: limit (default 20)
  404 if topic not found.
  Return posts for that topic ordered by score DESC.
  Cache with @cache(expire=300).

Step 12: Write backend/app/main.py
FastAPI app, title "Trend Lens API", version "1.0.0".
Lifespan:
  startup: create DB tables, init fastapi-cache2 with RedisBackend,
    call scheduler.start()
  shutdown: call scheduler.stop()
CORS middleware using settings.CORS_ORIGINS.
Include routers from trends.py and topics.py with prefix /api.
GET /api/health — checks DB + Redis, returns { status, db, redis, timestamp }
GET / — returns { message: "Trend Lens API", docs: "/docs" }

After Step 12: run:
  uvicorn app.main:app --reload --port 8000
  curl http://localhost:8000/api/health
  curl http://localhost:8000/api/trends
  curl http://localhost:8000/api/topics
Fix any errors before continuing.

---

PHASE 5 — React frontend

Step 13: Write frontend/package.json
Dependencies: react, react-dom, react-router-dom, swr, recharts, d3,
tailwindcss, autoprefixer, postcss
devDependencies: vite, @vitejs/plugin-react

Step 14: Write frontend/vite.config.js
React plugin. Proxy /api → http://localhost:8000 in dev.

Step 15: Write frontend/index.html
Minimal shell. Title "Trend Lens". Loads src/main.jsx.

Step 16: Write frontend/src/main.jsx
Render App inside BrowserRouter and React.StrictMode.

Step 17: Write frontend/src/App.jsx
React Router routes: / → Dashboard, /topic/:id → TopicDetail.
Persistent header: "Trend Lens" title + nav link home.

Step 18: Write frontend/src/hooks/useTrends.js
useTrends(source="all", hours=24) → SWR, /api/trends, refreshInterval 300000
useTopics(hours=24) → SWR, /api/topics, refreshInterval 900000
useTopicPosts(topicId) → SWR, /api/topics/${topicId}/posts, refreshInterval 300000
All hooks: return { data, error, isLoading }.

Step 19: Write frontend/src/components/FilterBar.jsx
Source buttons: All / Reddit / HN / GitHub
Time range buttons: 6h / 24h / 48h / 7d
Props: { source, setSource, hours, setHours }
Active button has distinct Tailwind background.

Step 20: Write frontend/src/components/TrendCard.jsx
Props: { post }
Source badge pill: Reddit=orange, HN=yellow, GitHub=gray (Tailwind colors)
Sentiment dot: green > 0.05, red < -0.05, gray otherwise
Title links to post.url (target="_blank", rel="noopener noreferrer")
Shows score and author below title.

Step 21: Write frontend/src/components/TrendChart.jsx
Props: { posts }
Group posts into hourly buckets by fetched_at, split by source.
Recharts LineChart: x=hour label, y=count.
3 lines: reddit (orange), hn (yellow), github (gray).
Legend, Tooltip, XAxis, YAxis, CartesianGrid.
ResponsiveContainer width="100%" height={300}.

Step 22: Write frontend/src/components/TopicBubble.jsx
Props: { topics, onTopicClick }
D3 d3.pack() layout. Each bubble = one topic.
Size = topic.post_count. Color = sentiment (green/red/gray).
Label inside bubble if radius > 30px, else hidden.
On click: call onTopicClick(topic.id).
SVG responsive, height=400.

Step 23: Write frontend/src/components/SentimentBar.jsx
Props: { topics }
Recharts BarChart. x=topic label truncated to 12 chars, y=avg_sentiment.
Bar fill: green if positive, red if negative.
Tooltip: full label + sentiment to 2 decimal places.
ResponsiveContainer width="100%" height={250}.

Step 24: Write frontend/src/pages/Dashboard.jsx
State: source="all", hours=24.
Use useTrends(source, hours) and useTopics(hours).
Layout:
  FilterBar at top
  3 stat cards: Total Posts | Avg Sentiment | Topics Found
  TrendChart (full width)
  TopicBubble (60% width) + SentimentBar (40% width) side by side
  Grid of top 20 TrendCards (2 columns)
Loading: animated gray skeleton divs.
Error: red banner with error.message.

Step 25: Write frontend/src/pages/TopicDetail.jsx
useParams() for id. useTopicPosts(id) and useTopics().
Heading: topic label.
Top keywords as Tailwind pill badges.
Avg sentiment with colored indicator and numeric value.
List of TrendCards for all posts in topic.
Back button → navigate("/").

After Step 25: run:
  cd frontend && npm install && npm run dev
Open browser at localhost:5173.
Confirm Dashboard loads, FilterBar works, no console errors.
Fix any errors before finishing.

---

PHASE 6 — Docker + final wiring

Step 26: Write backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

Step 27: Write docker-compose.yml at project root
Services:
  db: postgres:15, POSTGRES_DB=trendlens, named volume, port 5432
  redis: redis:7-alpine, port 6379
  backend: build from backend/, depends_on db + redis,
    port 8000:8000, env_file .env, restart unless-stopped

Step 28: Write .env.example
Every variable from config.py with placeholder values and
a comment on each line explaining what it is and where to get it.

Final check — run:
  docker-compose up --build
  curl http://localhost:8000/api/health
  curl http://localhost:8000/api/trends
Confirm { status: "ok" } and no errors.
Report a summary of everything built.