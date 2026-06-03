"""
NLP module for Trend Lens backend.

Handles text cleaning, keyword extraction via spaCy noun chunks, and sentiment
scoring via VADER. process_posts() is the main entry point that enriches a list
of post dicts with sentiment scores and extracted keywords. These enriched posts
are then passed to the clustering pipeline in cluster.py.
"""

import logging
import re

import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# Precompiled regex patterns for text cleaning
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
HTML_PATTERN = re.compile(r"<[^>]+>")
SPECIAL_CHARS_PATTERN = re.compile(r"[^a-zA-Z0-9\s]")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """
    Clean raw text for NLP processing.

    Strips URLs, HTML tags, special characters, and extra whitespace.
    Returns lowercased cleaned text.
    """
    if not text:
        return ""

    text = URL_PATTERN.sub("", text)
    text = HTML_PATTERN.sub("", text)
    text = SPECIAL_CHARS_PATTERN.sub(" ", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    text = text.lower().strip()

    return text


def extract_keywords(text: str, nlp_model: spacy.language.Language) -> list[str]:
    """
    Extract keywords from text using spaCy noun chunks.

    Filters out stopwords and chunks shorter than 2 characters.
    Keeps chunks with 1-3 words. Returns lowercase stripped list.
    """
    if not text:
        return []

    cleaned = clean_text(text)
    doc = nlp_model(cleaned)

    keywords: list[str] = []
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip().lower()

        # Skip short chunks
        if len(chunk_text) < 2:
            continue

        # Keep only chunks with 1-3 words
        words = chunk_text.split()
        if len(words) > 3:
            continue

        # Filter out stopwords-only chunks
        non_stop_words = [w for w in words if not nlp_model.vocab[w].is_stop]
        if not non_stop_words:
            continue

        keywords.append(chunk_text)

    return keywords


def score_sentiment(text: str, analyzer: SentimentIntensityAnalyzer) -> float:
    """
    Calculate VADER compound sentiment score for the given text.

    Uses raw text (not cleaned) because VADER works better with
    natural punctuation and capitalization. Returns a float from -1 to +1.
    """
    if not text:
        return 0.0

    scores = analyzer.polarity_scores(text)
    return scores["compound"]


def process_posts(posts: list[dict]) -> list[dict]:
    """
    Enrich a list of post dicts with sentiment scores and keywords.

    Loads spaCy model and VADER analyzer once, then processes each post.
    Adds 'sentiment' (float) and 'keywords' (list[str]) to each post dict.
    Returns the enriched list.
    """
    if not posts:
        return posts

    # Load models once
    logger.info("NLP: loading spaCy model and VADER analyzer")
    nlp_model = spacy.load("en_core_web_sm")
    analyzer = SentimentIntensityAnalyzer()

    enriched_posts: list[dict] = []
    for post in posts:
        try:
            # Sentiment on raw title (VADER works better with natural text)
            title = post.get("title", "")
            sentiment = score_sentiment(title, analyzer)

            # Keywords from title + raw_text combined
            raw_text = post.get("raw_text", "")
            combined_text = f"{title} {raw_text}"
            keywords = extract_keywords(combined_text, nlp_model)

            enriched_post = {**post, "sentiment": sentiment, "keywords": keywords}
            enriched_posts.append(enriched_post)
        except Exception as e:
            logger.error("NLP: failed to process post '%s' — %s", post.get("title", ""), e)
            enriched_posts.append({**post, "sentiment": 0.0, "keywords": []})

    logger.info("NLP: processed %d posts", len(enriched_posts))
    return enriched_posts


if __name__ == "__main__":
    # Test with 3 sample titles
    logging.basicConfig(level=logging.INFO)

    sample_posts = [
        {
            "title": "Rust is amazing for systems programming!",
            "raw_text": "I've been using Rust for 6 months and the borrow checker is fantastic.",
            "source": "reddit",
        },
        {
            "title": "Why Python is terrible for large codebases",
            "raw_text": "Type hints help but dynamic typing causes too many runtime errors.",
            "source": "hn",
        },
        {
            "title": "New React 19 features: Server Components and Actions",
            "raw_text": "React 19 introduces server components and form actions for better SSR.",
            "source": "github",
        },
    ]

    results = process_posts(sample_posts)
    for post in results:
        print(f"\n--- {post['source'].upper()} ---")
        print(f"  Title:     {post['title']}")
        print(f"  Sentiment: {post['sentiment']:.4f}")
        print(f"  Keywords:  {post['keywords']}")
