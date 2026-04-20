#!/usr/bin/env python3
"""Build the daily public SimpliXio artifact (json + md + html).

Monorepo-aware source order:
1) latest growth output metadata from ../growth_output/YYYY-MM-DD/*.json
2) fallback: latest JSON from CORTEX_OUTPUTS_DIR
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTOMATION_ROOT.parent

INPUT_FILTERED_DIR = AUTOMATION_ROOT / "output" / "filtered_signals"
OUTPUT_DIR = AUTOMATION_ROOT / "output" / "cortex_today"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
GROWTH_OUTPUT_DIR = REPO_ROOT / "growth_output"


def latest_file(directory: Path, pattern: str) -> Path:
    files = sorted(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No file matching {pattern} in {directory}")
    return files[-1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def maybe_run_growth_loop() -> None:
    script = REPO_ROOT / "scripts" / "cortex_growth_loop.py"
    if not script.exists():
        return
    subprocess.run(
        ["python3", str(script), "--max-items", "6"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def latest_growth_meta() -> dict[str, Any] | None:
    candidates: list[Path] = []
    if GROWTH_OUTPUT_DIR.exists():
        for day_dir in GROWTH_OUTPUT_DIR.glob("*"):
            if not day_dir.is_dir():
                continue
            for name in ("ready_to_publish.json", "pending_approval.json"):
                path = day_dir / name
                if path.exists():
                    candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime)
    return load_json(candidates[-1])


def compact_priorities(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    compact: list[dict[str, str]] = []
    for item in items:
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        compact.append(
            {
                "title": title,
                "why": str(item.get("why", "")).strip() or "High decision impact.",
                "action": str(item.get("action", "")).strip() or "Take the next concrete step.",
            }
        )
        if len(compact) >= 3:
            break
    return compact


def load_today_source() -> dict[str, Any]:
    meta = latest_growth_meta()
    if meta:
        today = meta.get("today", {})
        return {
            "date": today.get("date", datetime.now(UTC).strftime("%Y-%m-%d")),
            "priorities": compact_priorities(today.get("priorities", [])),
            "ignored_signals": [str(x) for x in today.get("ignored_signals", []) if str(x).strip()],
        }

    outputs_dir = Path(os.getenv("CORTEX_OUTPUTS_DIR", str(REPO_ROOT / "content" / "cortex_outputs")))
    if outputs_dir.exists():
        brief_file = latest_file(outputs_dir, "*.json")
        brief = load_json(brief_file)
        return {
            "date": brief.get("date", datetime.now(UTC).strftime("%Y-%m-%d")),
            "priorities": compact_priorities(brief.get("priorities", [])),
            "ignored_signals": [str(x) for x in brief.get("ignored_signals", []) if str(x).strip()],
        }

    raise FileNotFoundError("No daily source found in growth_output or CORTEX_OUTPUTS_DIR.")


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# SimpliXio Today · {payload['date']}")
    lines.append("")
    lines.append("## Top priorities")
    lines.append("")

    for idx, item in enumerate(payload["priorities"], start=1):
        lines.append(f"### {idx}. {item['title']}")
        lines.append(f"- Why: {item['why']}")
        lines.append(f"- Action: {item['action']}")
        lines.append("")

    lines.append("## Ignored today")
    lines.append("")
    lines.append(f"- {payload['ignored_signals_count']} weak signals removed")
    lines.append("")

    if payload["core_signals"]:
        lines.append("## Core signals")
        lines.append("")
        for signal in payload["core_signals"][:5]:
            lines.append(f"- {signal['title']}")
        lines.append("")

    lines.append("## Lesson")
    lines.append("")
    lines.append(f"- {payload['lesson']}")
    lines.append("")

    return "\n".join(lines)


def build_html(payload: dict[str, Any]) -> str:
    priority_blocks = []
    for idx, item in enumerate(payload["priorities"], start=1):
        priority_blocks.append(
            f"""
            <section class="card">
              <h2>{idx}. {item['title']}</h2>
              <p><strong>Why:</strong> {item['why']}</p>
              <p><strong>Action:</strong> {item['action']}</p>
            </section>
            """
        )

    core_signals = "".join(f"<li>{signal['title']}</li>" for signal in payload["core_signals"][:5])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SimpliXio Today · {payload['date']}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0b1220;
      color: #eef2ff;
      max-width: 820px;
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
  <h1>SimpliXio Today</h1>
  <p class="meta">{payload['date']}</p>
  {''.join(priority_blocks)}
  <section class="card">
    <h2>Ignored today</h2>
    <p>{payload['ignored_signals_count']} weak signals removed.</p>
  </section>
  <section class="card">
    <h2>Core signals</h2>
    <ul>{core_signals}</ul>
  </section>
  <section class="card">
    <h2>Lesson</h2>
    <p>{payload['lesson']}</p>
  </section>
</body>
</html>
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        today_source = load_today_source()
    except FileNotFoundError:
        # Try generating daily output once, then retry.
        maybe_run_growth_loop()
        today_source = load_today_source()

    filtered_file = latest_file(INPUT_FILTERED_DIR, "*_filtered.json")
    filtered = load_json(filtered_file)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "date": today_source["date"],
        "priorities": today_source["priorities"][:3],
        "ignored_signals_count": len(filtered.get("ignore", [])),
        "core_signals": filtered.get("core", []),
        "lesson": (
            "Reduce noise first. Better decisions start when weak signals are removed."
            if len(filtered.get("ignore", [])) > 0
            else "Clarity compounds when signal stays strong."
        ),
        "ignored_signals": today_source.get("ignored_signals", []),
    }

    json_path = OUTPUT_DIR / "cortex_today.json"
    md_path = OUTPUT_DIR / "cortex_today.md"
    html_path = OUTPUT_DIR / "cortex_today.html"

    json_text = json.dumps(payload, indent=2)
    md_text = build_markdown(payload)
    html_text = build_html(payload)

    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")

    day_key = payload["date"]
    (ARCHIVE_DIR / f"cortex_today_{day_key}.json").write_text(json_text, encoding="utf-8")
    (ARCHIVE_DIR / f"cortex_today_{day_key}.md").write_text(md_text, encoding="utf-8")
    (ARCHIVE_DIR / f"cortex_today_{day_key}.html").write_text(html_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "filtered_file": str(filtered_file),
                "output": {
                    "json": str(json_path),
                    "md": str(md_path),
                    "html": str(html_path),
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
