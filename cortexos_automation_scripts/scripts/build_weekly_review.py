#!/usr/bin/env python3
"""Build weekly review artifacts from the last 7 days of CortexOS Today outputs."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
CORTEX_TODAY_DIR = AUTOMATION_ROOT / "output" / "cortex_today"
CORTEX_TODAY_ARCHIVE_DIR = CORTEX_TODAY_DIR / "archive"
WEEKLY_REVIEW_DIR = AUTOMATION_ROOT / "output" / "weekly_review"
WEEKLY_REVIEW_ARCHIVE_DIR = WEEKLY_REVIEW_DIR / "archive"

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "for",
    "in",
    "on",
    "with",
    "from",
    "into",
    "what",
    "why",
    "how",
    "your",
    "today",
    "build",
    "better",
    "more",
    "less",
    "system",
    "signals",
    "signal",
    "priority",
    "priorities",
}


def ensure_dirs() -> None:
    WEEKLY_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    WEEKLY_REVIEW_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def parse_iso_date(value: str) -> date:
    return datetime.fromisoformat(value).date()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_daily_payloads() -> list[dict[str, Any]]:
    payloads_by_date: dict[str, dict[str, Any]] = {}

    for directory in (CORTEX_TODAY_DIR, CORTEX_TODAY_ARCHIVE_DIR):
        if not directory.exists():
            continue
        for path in directory.glob("*.json"):
            try:
                payload = load_json(path)
            except Exception:
                continue
            payload_date = str(payload.get("date", "")).strip()
            if payload_date:
                payloads_by_date[payload_date] = payload

    payloads = list(payloads_by_date.values())
    payloads.sort(key=lambda item: item["date"])
    return payloads


def last_7_days(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not payloads:
        return []
    latest = parse_iso_date(payloads[-1]["date"])
    start = latest - timedelta(days=6)
    return [item for item in payloads if start <= parse_iso_date(item["date"]) <= latest]


def tokenise(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def extract_keywords(text: str) -> list[str]:
    return [token for token in tokenise(text) if token not in STOPWORDS and len(token) > 2]


def build_recommendations(
    repeated_priorities: list[tuple[str, int]],
    repeated_signals: list[tuple[str, int]],
    total_ignored: int,
) -> list[str]:
    recommendations: list[str] = []

    if repeated_priorities:
        recommendations.append(
            f"Promote '{repeated_priorities[0][0]}' from recurring priority into a stronger product or architecture decision."
        )
    if repeated_signals:
        recommendations.append(
            f"Review recurring signal '{repeated_signals[0][0]}' and decide whether it changes roadmap or positioning."
        )
    if total_ignored > 20:
        recommendations.append(
            "Filtering removed many weak signals. Keep surfacing this as public proof of decision quality."
        )
    if not recommendations:
        recommendations.append(
            "Keep collecting daily outputs. Not enough repetition yet for a strategic adjustment."
        )
    return recommendations


def build_summary(
    days_covered: int,
    repeated_priorities: list[tuple[str, int]],
    repeated_signals: list[tuple[str, int]],
    total_ignored: int,
) -> str:
    if days_covered == 0:
        return "No weekly data available."

    parts = [
        f"CortexOS reviewed {days_covered} day(s) of output.",
        f"It ignored {total_ignored} weak signal(s) this week.",
    ]
    if repeated_priorities:
        parts.append(
            f"Top repeated priority: '{repeated_priorities[0][0]}' ({repeated_priorities[0][1]} time(s))."
        )
    if repeated_signals:
        parts.append(
            f"Top recurring signal: '{repeated_signals[0][0]}' ({repeated_signals[0][1]} mention(s))."
        )
    parts.append(
        "Focus remains unchanged: reduce noise, improve decisions, and strengthen daily reliability."
    )
    return " ".join(parts)


def build_review_payload(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    if not payloads:
        raise FileNotFoundError("No CortexOS daily outputs were found.")

    week_payloads = last_7_days(payloads)
    if not week_payloads:
        raise RuntimeError("No daily outputs were found for the last 7 days.")

    priority_counter: Counter[str] = Counter()
    signal_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()
    total_ignored = 0
    priorities_reviewed = 0

    for payload in week_payloads:
        total_ignored += int(payload.get("ignored_signals_count", 0))

        for priority in payload.get("priorities", []):
            title = str(priority.get("title", "")).strip()
            if not title:
                continue
            priorities_reviewed += 1
            priority_counter[title] += 1
            for keyword in extract_keywords(title):
                keyword_counter[keyword] += 1

        for signal in payload.get("core_signals", []):
            title = str(signal.get("title", "")).strip()
            if title:
                signal_counter[title] += 1

    top_priorities = priority_counter.most_common(5)
    top_signals = signal_counter.most_common(5)
    top_keywords = keyword_counter.most_common(8)

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "week_start": week_payloads[0]["date"],
        "week_end": week_payloads[-1]["date"],
        "days_covered": len(week_payloads),
        "priorities_reviewed": priorities_reviewed,
        "total_ignored_signals": total_ignored,
        "top_priorities": [{"title": title, "count": count} for title, count in top_priorities],
        "top_signals": [{"title": title, "count": count} for title, count in top_signals],
        "top_keywords": [{"keyword": keyword, "count": count} for keyword, count in top_keywords],
        "summary": build_summary(len(week_payloads), top_priorities, top_signals, total_ignored),
        "recommendations": build_recommendations(top_priorities, top_signals, total_ignored),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# CortexOS Weekly Review · {payload['week_start']} → {payload['week_end']}",
        "",
        "## Summary",
        "",
        payload["summary"],
        "",
        "## Top priorities",
        "",
    ]

    top_priorities = payload.get("top_priorities", [])
    if top_priorities:
        for item in top_priorities:
            lines.append(f"- {item['title']} ({item['count']})")
    else:
        lines.append("- None")

    lines.extend(["", "## Top signals", ""])
    top_signals = payload.get("top_signals", [])
    if top_signals:
        for item in top_signals:
            lines.append(f"- {item['title']} ({item['count']})")
    else:
        lines.append("- None")

    lines.extend(["", "## Top keywords", ""])
    top_keywords = payload.get("top_keywords", [])
    if top_keywords:
        for item in top_keywords:
            lines.append(f"- {item['keyword']} ({item['count']})")
    else:
        lines.append("- None")

    lines.extend(["", "## Recommendations", ""])
    for item in payload.get("recommendations", []):
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            f"Total ignored signals: {payload['total_ignored_signals']}",
            f"Priorities reviewed: {payload['priorities_reviewed']}",
            "",
        ]
    )

    return "\n".join(lines)


def render_html(payload: dict[str, Any]) -> str:
    def li_block(items: list[dict[str, Any]], key: str) -> str:
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{item[key]} ({item['count']})</li>" for item in items)

    recs = "".join(f"<li>{item}</li>" for item in payload.get("recommendations", []))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CortexOS Weekly Review</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0b1220;
      color: #eef2ff;
      max-width: 860px;
      margin: 40px auto;
      padding: 0 20px;
      line-height: 1.6;
    }}
    .card {{
      background: #121b2f;
      border-radius: 18px;
      padding: 20px;
      margin-bottom: 18px;
    }}
    .meta {{
      color: #a7b3d1;
    }}
    h1, h2 {{
      margin-top: 0;
    }}
  </style>
</head>
<body>
  <h1>CortexOS Weekly Review</h1>
  <p class="meta">{payload['week_start']} → {payload['week_end']}</p>

  <section class="card">
    <h2>Summary</h2>
    <p>{payload['summary']}</p>
  </section>

  <section class="card">
    <h2>Top priorities</h2>
    <ul>{li_block(payload.get('top_priorities', []), 'title')}</ul>
  </section>

  <section class="card">
    <h2>Top signals</h2>
    <ul>{li_block(payload.get('top_signals', []), 'title')}</ul>
  </section>

  <section class="card">
    <h2>Top keywords</h2>
    <ul>{li_block(payload.get('top_keywords', []), 'keyword')}</ul>
  </section>

  <section class="card">
    <h2>Recommendations</h2>
    <ul>{recs}</ul>
  </section>

  <section class="card">
    <h2>Metrics</h2>
    <p>Total ignored signals: {payload['total_ignored_signals']}</p>
    <p>Priorities reviewed: {payload['priorities_reviewed']}</p>
    <p>Days covered: {payload['days_covered']}</p>
  </section>
</body>
</html>
"""


def save_outputs(payload: dict[str, Any]) -> None:
    week_key = f"{payload['week_start']}_to_{payload['week_end']}"

    json_text = json.dumps(payload, indent=2)
    md_text = render_markdown(payload)
    html_text = render_html(payload)

    (WEEKLY_REVIEW_DIR / "latest.json").write_text(json_text, encoding="utf-8")
    (WEEKLY_REVIEW_DIR / "latest.md").write_text(md_text, encoding="utf-8")
    (WEEKLY_REVIEW_DIR / "latest.html").write_text(html_text, encoding="utf-8")

    (WEEKLY_REVIEW_ARCHIVE_DIR / f"{week_key}.json").write_text(json_text, encoding="utf-8")
    (WEEKLY_REVIEW_ARCHIVE_DIR / f"{week_key}.md").write_text(md_text, encoding="utf-8")
    (WEEKLY_REVIEW_ARCHIVE_DIR / f"{week_key}.html").write_text(html_text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    payloads = find_daily_payloads()
    review = build_review_payload(payloads)
    save_outputs(review)

    print(
        json.dumps(
            {
                "status": "ok",
                "week_start": review["week_start"],
                "week_end": review["week_end"],
                "days_covered": review["days_covered"],
                "output_dir": str(WEEKLY_REVIEW_DIR),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
