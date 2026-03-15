#!/usr/bin/env python3
"""
Weekly Digest Generator
-----------------------
Fetches AI news via RSS and trending GitHub repos, then writes
a markdown digest file. CortexOS uses this as the primary input
for the scoring → focus recommendation pipeline.

Usage:
    python3 scripts/weekly_digest.py

Sources are tuned for AI systems engineering signal.
"""

import os
from datetime import UTC, datetime

import feedparser
import requests

# ── High-signal RSS sources ────────────────────────────────────

RSS_FEEDS = [
    # AI companies & research
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/news/rss",
    "https://ai.meta.com/blog/rss/",
    "https://blog.google/technology/ai/rss/",
    # AI dev ecosystem
    "https://huggingface.co/blog/feed.xml",
    # AI engineering & research
    "https://paperswithcode.com/rss",
    # General tech (filtered later by scoring engine)
    "https://www.techcrunch.com/feed/",
    "https://news.ycombinator.com/rss",
]

GITHUB_TRENDING_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def fetch_rss_articles(feeds: list[str], max_entries: int = 10) -> list[str]:
    """Fetch recent articles from RSS feeds."""
    entries = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_entries]:
                published = entry.published if hasattr(entry, "published") else ""
                title = entry.title.strip() if hasattr(entry, "title") else "Untitled"
                link = entry.link if hasattr(entry, "link") else ""
                entries.append(f"- [{title}]({link}) — {published}")
        except Exception as e:
            print(f"Warning: Failed to fetch {url}: {e}")
    return entries


def fetch_github_trending(topic: str = "ai", max_repos: int = 5) -> list[str]:
    """Fetch trending AI repositories from GitHub."""
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    params = {
        "q": f"topic:{topic} created:>={datetime.utcnow().date()}",
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos,
    }

    try:
        resp = requests.get(GITHUB_TRENDING_URL, headers=headers, params=params, timeout=15)
        items = resp.json().get("items", [])
        return [f"- **{item['full_name']}** ({item['stargazers_count']} stars) — {item['html_url']}" for item in items]
    except Exception as e:
        print(f"Warning: GitHub trending fetch failed: {e}")
        return []


def generate_digest() -> str:
    """Build the full digest markdown string."""
    news = fetch_rss_articles(RSS_FEEDS)
    trending = fetch_github_trending()
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    sections = [
        f"# Weekly AI Digest — {today}",
        "",
        "## Recent articles",
        "\n".join(news) if news else "_No articles fetched._",
        "",
        "## Trending GitHub repositories",
        "\n".join(trending) if trending else "_No trending repos fetched._",
    ]

    return "\n".join(sections)


if __name__ == "__main__":
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    content = generate_digest()
    filename = f"weekly_digest_{today}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Digest written to {filename}")
