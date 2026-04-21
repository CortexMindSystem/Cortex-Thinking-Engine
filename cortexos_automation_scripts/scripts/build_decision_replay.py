#!/usr/bin/env python3
"""Build Decision Replay artifacts from real SimpliXio outputs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
FILTERED_DIR = AUTOMATION_ROOT / "output" / "filtered_signals"
TODAY_DIR = AUTOMATION_ROOT / "output" / "cortex_today"
REPLAY_DIR = AUTOMATION_ROOT / "output" / "decision_replay"
REPLAY_ARCHIVE_DIR = REPLAY_DIR / "archive"


def latest_file(directory: Path, pattern: str) -> Path:
    files = sorted(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No file matching {pattern} in {directory}")
    return files[-1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(today: dict[str, Any], filtered: dict[str, Any]) -> dict[str, Any]:
    kept = list(filtered.get("core", [])) + list(filtered.get("adjacent", []))
    ignored = list(filtered.get("ignore", []))
    priorities = list(today.get("priorities", []))

    kept_signals = [
        {
            "title": str(item.get("title", "")).strip(),
            "reason": "Mapped to active context or related to current goals.",
        }
        for item in kept
        if str(item.get("title", "")).strip()
    ][:5]

    ignored_signals = [
        {
            "title": str(item.get("title", "")).strip(),
            "reason": "Weak relevance to current decision context.",
        }
        for item in ignored
        if str(item.get("title", "")).strip()
    ][:5]

    final_priorities = [
        {
            "title": str(item.get("title", "")).strip(),
            "why": str(item.get("why", "")).strip(),
            "action": str(item.get("action", "")).strip(),
        }
        for item in priorities
        if str(item.get("title", "")).strip()
    ][:3]

    signals_kept = len(kept_signals)
    signals_ignored = len(ignored_signals)
    signals_reviewed = signals_kept + signals_ignored
    replay_date = str(today.get("date", datetime.now(UTC).strftime("%Y-%m-%d")))

    summary = (
        f"SimpliXio reviewed {signals_reviewed} signals, ignored {signals_ignored}, and selected {len(final_priorities)} priorities."
    )

    return {
        "date": replay_date,
        "signals_reviewed": signals_reviewed,
        "signals_kept": signals_kept,
        "signals_ignored": signals_ignored,
        "kept_signals": kept_signals,
        "ignored_signals": ignored_signals,
        "final_priorities": final_priorities,
        "summary": summary,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# SimpliXio Decision Replay · {payload['date']}",
        "",
        payload["summary"],
        "",
        "## Metrics",
        "",
        f"- Signals reviewed: {payload['signals_reviewed']}",
        f"- Signals kept: {payload['signals_kept']}",
        f"- Signals ignored: {payload['signals_ignored']}",
        "",
        "## Kept signals",
        "",
    ]

    if payload["kept_signals"]:
        for item in payload["kept_signals"]:
            lines.append(f"- {item['title']} — {item['reason']}")
    else:
        lines.append("- None")

    lines.extend(["", "## Ignored signals", ""])
    if payload["ignored_signals"]:
        for item in payload["ignored_signals"]:
            lines.append(f"- {item['title']} — {item['reason']}")
    else:
        lines.append("- None")

    lines.extend(["", "## Final priorities", ""])
    if payload["final_priorities"]:
        for idx, item in enumerate(payload["final_priorities"], start=1):
            lines.append(f"### {idx}. {item['title']}")
            lines.append(f"- Why: {item['why']}")
            lines.append(f"- Action: {item['action']}")
            lines.append("")
    else:
        lines.append("- None")

    return "\n".join(lines).strip() + "\n"


def render_html(payload: dict[str, Any]) -> str:
    def list_block(items: list[dict[str, str]], field: str) -> str:
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{item[field]}</li>" for item in items)

    priorities_html = ""
    if payload["final_priorities"]:
        priorities_html = "".join(
            f"<li><strong>{item['title']}</strong><br/>Why: {item['why']}<br/>Action: {item['action']}</li>"
            for item in payload["final_priorities"]
        )
    else:
        priorities_html = "<li>None</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SimpliXio Decision Replay</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0b1220;
      color: #eef2ff;
      max-width: 840px;
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
  </style>
</head>
<body>
  <h1>SimpliXio Decision Replay</h1>
  <section class="card">
    <p>{payload['summary']}</p>
    <p>Signals reviewed: {payload['signals_reviewed']}</p>
    <p>Signals kept: {payload['signals_kept']}</p>
    <p>Signals ignored: {payload['signals_ignored']}</p>
  </section>
  <section class="card">
    <h2>Kept signals</h2>
    <ul>{list_block(payload['kept_signals'], 'title')}</ul>
  </section>
  <section class="card">
    <h2>Ignored signals</h2>
    <ul>{list_block(payload['ignored_signals'], 'title')}</ul>
  </section>
  <section class="card">
    <h2>Final priorities</h2>
    <ul>{priorities_html}</ul>
  </section>
</body>
</html>
"""


def save_outputs(payload: dict[str, Any]) -> dict[str, str]:
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    REPLAY_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    day_key = payload["date"]
    latest_json = REPLAY_DIR / "latest.json"
    latest_md = REPLAY_DIR / "latest.md"
    latest_html = REPLAY_DIR / "latest.html"

    json_text = json.dumps(payload, indent=2)
    md_text = render_markdown(payload)
    html_text = render_html(payload)

    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")
    latest_html.write_text(html_text, encoding="utf-8")

    (REPLAY_ARCHIVE_DIR / f"decision_replay_{day_key}.json").write_text(
        json_text, encoding="utf-8"
    )
    (REPLAY_ARCHIVE_DIR / f"decision_replay_{day_key}.md").write_text(
        md_text, encoding="utf-8"
    )
    (REPLAY_ARCHIVE_DIR / f"decision_replay_{day_key}.html").write_text(
        html_text, encoding="utf-8"
    )

    return {
        "json": str(latest_json),
        "md": str(latest_md),
        "html": str(latest_html),
    }


def main() -> None:
    try:
        filtered_file = latest_file(FILTERED_DIR, "*_filtered.json")
        today_file = latest_file(TODAY_DIR, "cortex_today.json")
    except FileNotFoundError as exc:
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": str(exc),
                },
                indent=2,
            )
        )
        return

    filtered = load_json(filtered_file)
    today = load_json(today_file)
    payload = build_payload(today, filtered)
    outputs = save_outputs(payload)

    print(
        json.dumps(
            {
                "status": "ok",
                "date": payload["date"],
                "signals_reviewed": payload["signals_reviewed"],
                "signals_ignored": payload["signals_ignored"],
                "signals_kept": payload["signals_kept"],
                "output": outputs,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

