# 📈 Trend Lens

A real-time tech trend dashboard that scrapes **Reddit**, **Hacker News**, and **GitHub Trending**, runs an NLP pipeline on the posts, and displays interactive visualizations of what's trending in tech.

![Dashboard](https://img.shields.io/badge/status-active-brightgreen) ![Python](https://img.shields.io/badge/python-3.11+-blue) ![React](https://img.shields.io/badge/react-18-61dafb) ![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

1. **Scrapes** top posts from 8 Reddit subreddits, HN top 100 stories, and GitHub Trending repos every 30 minutes
2. **Analyzes** each post with NLP — extracts keywords (spaCy) and sentiment scores (VADER)
3. **Clusters** posts into 8 topic groups using TF-IDF + KMeans
4. **Visualizes** everything in a React dashboard with interactive charts and filters

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy (async), APScheduler |
| **NLP** | spaCy, VADER Sentiment, scikit-learn (TF-IDF + KMeans) |
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts, D3.js |
| **Database** | PostgreSQL 15, Redis 7 (API cache) |
| **DevOps** | Docker, Docker Compose |

## Quick Start (Docker)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Node.js 18+](https://nodejs.org/) (for frontend dev server)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/trend-lens.git
cd trend-lens
cp .env.example .env
```

Edit `.env` and add your Reddit API credentials (optional — HN and GitHub work without them):
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=TrendLens/1.0 by YourUsername
```

> Get Reddit credentials at https://www.reddit.com/prefs/apps — create a "script" type app.

### 2. Start backend + databases

```bash
docker-compose up --build -d
```

This starts PostgreSQL, Redis, and the FastAPI backend on port 8000.

### 3. Verify backend is running

```bash
curl http://localhost:8000/api/health
# {"status":"ok","db":"ok","redis":"ok","timestamp":"..."}
```

### 4. Populate initial data

The scraper runs automatically every 30 minutes. To trigger it immediately:

```bash
curl -X POST http://localhost:8000/api/trigger-scrape
# {"status":"ok","message":"Scrape and NLP pipeline completed"}
```

### 5. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — you should see the dashboard with live data.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check (DB + Redis status) |
| `/api/trends` | GET | List posts — `?source=reddit\|hn\|github&hours=24&limit=50` |
| `/api/topics` | GET | Topic clusters — `?hours=24` |
| `/api/topics/{id}/posts` | GET | Posts in a specific topic — `?limit=20` |
| `/api/trigger-scrape` | POST | Manually trigger scrape + NLP pipeline |
| `/docs` | GET | Interactive Swagger API docs |

## Project Structure

```
trend-lens/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI app, lifespan, CORS, health check
│       ├── config.py         # Pydantic settings from .env
│       ├── database.py       # Async SQLAlchemy engine + sessions
│       ├── models.py         # Post & Topic ORM models
│       ├── scraper.py        # Reddit + HN + GitHub fetchers
│       ├── scheduler.py      # APScheduler (30 min interval)
│       ├── nlp.py            # Text cleaning, spaCy keywords, VADER sentiment
│       ├── cluster.py        # TF-IDF + KMeans clustering pipeline
│       └── routes/
│           ├── trends.py     # GET /api/trends
│           └── topics.py     # GET /api/topics
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx           # Layout + routing
│       ├── hooks/useTrends.js
│       ├── components/       # FilterBar, TrendCard, TrendChart, TopicBubble, SentimentBar
│       └── pages/            # Dashboard, TopicDetail
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Data Sources

| Source | Method | What's Scraped |
|--------|--------|---------------|
| **Reddit** | PRAW (OAuth) | Top 25 posts from r/programming, r/webdev, r/MachineLearning, r/Python, r/javascript, r/devops, r/golang, r/rust |
| **Hacker News** | Firebase REST API | Top 100 stories |
| **GitHub** | HTML scrape | Top 30 trending repos (daily, English) |

## NLP Pipeline

```
Scrape → Clean Text → Extract Keywords (spaCy) → Score Sentiment (VADER)
                                                         ↓
                                              TF-IDF + KMeans Clustering
                                                         ↓
                                              8 Topic Clusters with Labels
```

## Environment Variables

See [.env.example](.env.example) for all available configuration options.

## License

MIT
