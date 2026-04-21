#!/usr/bin/env python3
"""Collect acquisition signals from compliant public sources.

Explicitly does not scrape LinkedIn.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import feedparser
import requests
from dotenv import load_dotenv

from acquisition_crm import connect, init_db, upsert_lead, OUTPUT_DIR


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTOMATION_ROOT.parent


@dataclass
class RawSignal:
    source: str
    source_url: str
    title: str
    excerpt: str
    author_handle: str
    tags: list[str]
    observed_pain: str
    raw_payload: dict[str, Any]


def load_config() -> dict[str, Any]:
    load_dotenv(AUTOMATION_ROOT / ".env")
    return {
        "rss_feeds": [x.strip() for x in os.getenv("RSS_FEEDS", "").split(",") if x.strip()],
        "product_feeds": [x.strip() for x in os.getenv("PRODUCT_FEEDS", "").split(",") if x.strip()],
        "github_topics": [x.strip() for x in os.getenv("GITHUB_TOPICS", "ai,agents,developer-tools").split(",") if x.strip()],
        "github_token": os.getenv("GITHUB_TOKEN", "").strip(),
        "hn_enabled": os.getenv("HN_ENABLED", "true").lower() == "true",
        "max_per_source": int(os.getenv("ACQ_MAX_PER_SOURCE", "20")),
    }


def collect_rss(feeds: list[str], max_per_feed: int) -> list[RawSignal]:
    signals: list[RawSignal] = []
    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            continue
        for entry in parsed.entries[:max_per_feed]:
            title = str(getattr(entry, "title", "")).strip()
            link = str(getattr(entry, "link", "")).strip()
            if not title or not link:
                continue
            summary = str(getattr(entry, "summary", "")).strip()
            author = str(getattr(entry, "author", "")).strip()
            signals.append(
                RawSignal(
                    source="rss",
                    source_url=link,
                    title=title,
                    excerpt=summary[:500],
                    author_handle=author,
                    tags=["rss"],
                    observed_pain=detect_pain_signal(f"{title} {summary}"),
                    raw_payload={
                        "feed_url": feed_url,
                        "published": str(getattr(entry, "published", "")),
                    },
                )
            )
    return signals


def collect_github(topics: list[str], token: str, per_topic: int) -> list[RawSignal]:
    signals: list[RawSignal] = []
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for topic in topics:
        params = {
            "q": f"topic:{topic} stars:>20 pushed:>2025-01-01",
            "sort": "updated",
            "order": "desc",
            "per_page": per_topic,
        }
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                headers=headers,
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            continue

        for item in payload.get("items", []):
            title = str(item.get("full_name", "")).strip()
            url = str(item.get("html_url", "")).strip()
            description = str(item.get("description", "")).strip()
            if not title or not url:
                continue

            signals.append(
                RawSignal(
                    source="github",
                    source_url=url,
                    title=title,
                    excerpt=description[:500],
                    author_handle=str(item.get("owner", {}).get("login", "")).strip(),
                    tags=["github", topic],
                    observed_pain=detect_pain_signal(f"{title} {description}"),
                    raw_payload={
                        "stars": int(item.get("stargazers_count", 0)),
                        "forks": int(item.get("forks_count", 0)),
                        "updated_at": str(item.get("updated_at", "")),
                        "language": str(item.get("language", "")).strip(),
                        "topic": topic,
                    },
                )
            )
    return signals


def collect_hn(max_items: int) -> list[RawSignal]:
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=40",
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return []

    signals: list[RawSignal] = []
    for item in payload.get("hits", [])[:max_items]:
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "") or f"https://news.ycombinator.com/item?id={item.get('objectID', '')}").strip()
        if not title or not url:
            continue
        author = str(item.get("author", "")).strip()
        text = str(item.get("story_text", "")).strip()
        signals.append(
            RawSignal(
                source="hacker_news",
                source_url=url,
                title=title,
                excerpt=text[:500],
                author_handle=author,
                tags=["hacker_news"],
                observed_pain=detect_pain_signal(f"{title} {text}"),
                raw_payload={
                    "points": int(item.get("points", 0) or 0),
                    "num_comments": int(item.get("num_comments", 0) or 0),
                    "created_at": str(item.get("created_at", "")),
                },
            )
        )
    return signals


def collect_simplixio_artifacts(max_items: int) -> list[RawSignal]:
    signals: list[RawSignal] = []
    today_path = AUTOMATION_ROOT / "output" / "cortex_today" / "cortex_today.json"
    weekly_path = AUTOMATION_ROOT / "output" / "weekly_review" / "latest.json"
    publish_path = AUTOMATION_ROOT / "output" / "publish" / "latest_posts.json"

    if today_path.exists():
        try:
            payload = json.loads(today_path.read_text(encoding="utf-8"))
            for item in payload.get("priorities", [])[:max_items]:
                title = str(item.get("title", "")).strip()
                if not title:
                    continue
                why = str(item.get("why", "")).strip()
                signals.append(
                    RawSignal(
                        source="simplixio_today",
                        source_url="local://output/cortex_today/cortex_today.json",
                        title=title,
                        excerpt=why[:500],
                        author_handle="",
                        tags=["internal_artifact", "priority"],
                        observed_pain=detect_pain_signal(f"{title} {why}"),
                        raw_payload={"date": payload.get("date", "")},
                    )
                )
        except Exception:
            pass

    if weekly_path.exists():
        try:
            payload = json.loads(weekly_path.read_text(encoding="utf-8"))
            for item in payload.get("top_priorities", [])[:max_items]:
                title = str(item.get("title", "")).strip()
                if not title:
                    continue
                signals.append(
                    RawSignal(
                        source="simplixio_weekly_review",
                        source_url="local://output/weekly_review/latest.json",
                        title=title,
                        excerpt=str(payload.get("summary", "")).strip()[:500],
                        author_handle="",
                        tags=["internal_artifact", "weekly_review"],
                        observed_pain=detect_pain_signal(title),
                        raw_payload={"week_start": payload.get("week_start", ""), "week_end": payload.get("week_end", "")},
                    )
                )
        except Exception:
            pass

    if publish_path.exists():
        try:
            payload = json.loads(publish_path.read_text(encoding="utf-8"))
            for channel, item in payload.get("posts", {}).items():
                body = str(item.get("body", "")).strip()
                if not body:
                    continue
                title = str(item.get("title", "")).strip() or f"{channel} engagement draft"
                signals.append(
                    RawSignal(
                        source="simplixio_engagement",
                        source_url=f"local://output/publish/latest_posts.json#{channel}",
                        title=title,
                        excerpt=body[:500],
                        author_handle="",
                        tags=["internal_artifact", "engagement", channel],
                        observed_pain=detect_pain_signal(body),
                        raw_payload={"channel": channel},
                    )
                )
        except Exception:
            pass

    return signals


def detect_pain_signal(text: str) -> str:
    lowered = text.lower()
    pain_map = [
        ("decision fatigue", "Decision fatigue"),
        ("information overload", "Information overload"),
        ("too many tools", "Too many tools"),
        ("priorit", "Prioritisation pain"),
        ("context", "Missing context"),
        ("workflow", "Workflow fragmentation"),
        ("signal", "Signal vs noise"),
    ]
    for needle, label in pain_map:
        if needle in lowered:
            return label
    return "Unknown"


def dedupe_signals(items: list[RawSignal]) -> list[RawSignal]:
    seen: set[str] = set()
    out: list[RawSignal] = []
    for item in items:
        key = item.source_url.strip().lower() or f"{item.source}:{item.title.strip().lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def write_raw_archive(signals: list[RawSignal]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUTPUT_DIR / "raw" / f"lead_signals_{stamp}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "count": len(signals),
        "signals": [asdict(s) for s in signals],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def run() -> dict[str, Any]:
    cfg = load_config()
    signals: list[RawSignal] = []

    signals.extend(collect_rss(cfg["rss_feeds"], cfg["max_per_source"]))
    signals.extend(collect_rss(cfg["product_feeds"], cfg["max_per_source"]))
    signals.extend(collect_github(cfg["github_topics"], cfg["github_token"], cfg["max_per_source"]))
    if cfg["hn_enabled"]:
        signals.extend(collect_hn(cfg["max_per_source"]))
    signals.extend(collect_simplixio_artifacts(10))

    deduped = dedupe_signals(signals)
    raw_path = write_raw_archive(deduped)

    conn = connect()
    init_db(conn)
    before_count = int(conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0])
    upserted = 0
    for signal in deduped:
        upsert_lead(
            conn,
            source=signal.source,
            source_url=signal.source_url,
            title=signal.title,
            author_handle=signal.author_handle,
            pain_signal=signal.observed_pain,
            raw_payload={
                "excerpt": signal.excerpt,
                "tags": signal.tags,
                "raw": signal.raw_payload,
            },
        )
        upserted += 1
    after_count = int(conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0])
    newly_inserted = max(0, after_count - before_count)

    return {
        "status": "ok",
        "count": len(deduped),
        "upserted": upserted,
        "newly_inserted": newly_inserted,
        "raw_archive": str(raw_path),
    }


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
