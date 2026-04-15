#!/usr/bin/env python3
"""Quality gate for generated marketing drafts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
DRAFTS_DIR = AUTOMATION_ROOT / "output" / "drafts"
OUTPUT_DIR = AUTOMATION_ROOT / "output" / "quality_gate"

BANNED_PHRASES = {
    "revolutionary",
    "game-changer",
    "unleash",
    "supercharge",
    "transformative",
    "next-gen",
    "cutting-edge",
    "seamless",
}

REQUIRED_THEMES = {
    "decision",
    "signal",
    "noise",
    "priority",
    "context",
    "action",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quality checks on generated drafts.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero exit code when any draft fails quality checks.",
    )
    return parser.parse_args()


def load_drafts() -> dict[str, str]:
    drafts: dict[str, str] = {}
    if not DRAFTS_DIR.exists():
        raise FileNotFoundError(f"{DRAFTS_DIR} does not exist")
    for path in sorted(DRAFTS_DIR.glob("*.md")):
        drafts[path.name] = path.read_text(encoding="utf-8")
    return drafts


def analyse_text(text: str) -> dict[str, Any]:
    text_lower = text.lower()
    banned_hits = [phrase for phrase in BANNED_PHRASES if phrase in text_lower]
    required_hits = [theme for theme in REQUIRED_THEMES if theme in text_lower]

    sentence_count = max(1, len([x for x in re.split(r"[.!?]+", text) if x.strip()]))
    word_count = len(re.findall(r"[a-zA-Z0-9]+", text))

    score = 100
    score -= len(banned_hits) * 20
    if len(required_hits) < 2:
        score -= 25
    if word_count < 25:
        score -= 20
    if word_count > 220:
        score -= 10

    passed = score >= 70 and not banned_hits
    return {
        "passed": passed,
        "score": score,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "banned_hits": banned_hits,
        "required_hits": required_hits,
    }


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    drafts = load_drafts()
    report: dict[str, Any] = {filename: analyse_text(text) for filename, text in drafts.items()}

    totals = {
        "drafts": len(report),
        "passed": sum(1 for item in report.values() if item.get("passed")),
    }
    totals["failed"] = totals["drafts"] - totals["passed"]

    payload = {
        "summary": totals,
        "report": report,
    }
    out = OUTPUT_DIR / "quality_report.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))

    if args.strict and totals["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
