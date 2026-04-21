#!/usr/bin/env python3
"""Generate public acquisition content from real SimpliXio artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from acquisition_crm import OUTPUT_DIR, connect, init_db, insert_content, recent_content_hashes, text_hash


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
TODAY_PATH = AUTOMATION_ROOT / "output" / "cortex_today" / "cortex_today.json"
WEEKLY_PATH = AUTOMATION_ROOT / "output" / "weekly_review" / "latest.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_posts(today: dict[str, Any], weekly: dict[str, Any]) -> list[dict[str, str]]:
    priorities = today.get("priorities", [])[:3]
    ignored_count = int(today.get("ignored_signals_count", 0))
    summary = str(weekly.get("summary", "")).strip()
    repeated = ""
    if weekly.get("top_priorities"):
        repeated = str(weekly["top_priorities"][0].get("title", "")).strip()

    top1 = priorities[0] if priorities else {"title": "Reduce noise", "why": "Decision quality first.", "action": "Choose one concrete next step."}
    top2 = priorities[1] if len(priorities) > 1 else {"title": "Protect focus"}
    top3 = priorities[2] if len(priorities) > 2 else {"title": "Act on what matters"}

    x_post = (
        "SimpliXio today:\n\n"
        f"1) {top1['title']}\n"
        f"2) {top2['title']}\n"
        f"3) {top3['title']}\n\n"
        f"Why: {top1.get('why', 'Decision clarity compounds.')}\n"
        f"Next action: {top1.get('action', 'Take one concrete action now.')}\n"
        f"Ignored signals: {ignored_count}\n\n"
        "Decision system. Noise into action."
    )

    linkedin_post = (
        "SimpliXio is a decision system that turns noise into 3 priorities.\n\n"
        f"Today we ignored {ignored_count} weak signals.\n"
        f"Top priority: {top1['title']}\n"
        f"Why it matters: {top1.get('why', 'Decision quality improves with clearer signal.')}\n"
        f"What to do next: {top1.get('action', 'Take one concrete step.')}\n\n"
        + (f"Weekly repeat: {repeated}\n" if repeated else "")
        + (f"Weekly summary: {summary}\n\n" if summary else "\n")
        + "Not another AI app. A decision system for clearer action."
    )

    blog_post = (
        "# SimpliXio Today\n\n"
        "A decision system that turns noise into 3 priorities.\n\n"
        "## Priorities\n\n"
        + "\n".join(
            [
                f"### {idx + 1}. {item.get('title', '')}\n"
                f"- Why: {item.get('why', '')}\n"
                f"- Action: {item.get('action', '')}\n"
                for idx, item in enumerate(priorities)
            ]
        )
        + "\n\n"
        f"## Ignored signals\n\n- {ignored_count}\n\n"
        + ("## Weekly review\n\n" + summary + "\n" if summary else "")
    )

    return [
        {"channel": "x", "angle": "today_priority", "title": "SimpliXio Today", "body": x_post},
        {"channel": "linkedin", "angle": "proof_of_filtering", "title": "Noise into action", "body": linkedin_post},
        {"channel": "blog", "angle": "daily_artifact", "title": "SimpliXio Today artifact", "body": blog_post},
    ]


def run() -> dict[str, Any]:
    today = load_json(TODAY_PATH)
    weekly = load_json(WEEKLY_PATH)
    if not today:
        return {"status": "skipped", "reason": "missing_today_artifact"}

    posts = build_posts(today, weekly)
    conn = connect()
    init_db(conn)
    known_hashes = recent_content_hashes(conn, limit=80)

    created = 0
    skipped_repeated = 0
    outputs: list[dict[str, Any]] = []
    for post in posts:
        body_hash = text_hash(post["body"])
        if body_hash in known_hashes:
            skipped_repeated += 1
            continue
        content_id = insert_content(
            conn,
            channel=post["channel"],
            angle=post["angle"],
            title=post["title"],
            body=post["body"],
            source_artifact="cortex_today+weekly_review",
            status="draft",
        )
        created += 1
        known_hashes.add(body_hash)
        out_path = OUTPUT_DIR / "drafts" / f"acq_{post['channel']}_latest.md"
        out_path.write_text(post["body"], encoding="utf-8")
        outputs.append(
            {
                "content_id": content_id,
                "channel": post["channel"],
                "angle": post["angle"],
                "path": str(out_path),
            }
        )

    return {
        "status": "ok",
        "created": created,
        "skipped_repeated": skipped_repeated,
        "outputs": outputs,
    }


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
