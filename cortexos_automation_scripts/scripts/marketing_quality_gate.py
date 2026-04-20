#!/usr/bin/env python3
"""Quality gate for generated SimpliXio marketing drafts."""

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
MEMORY_PATH = AUTOMATION_ROOT / "output" / "memory" / "content_memory.json"
MANIFEST_PATH = AUTOMATION_ROOT / "output" / "publish" / "latest_posts.json"

BANNED_PHRASES = {
    "revolutionary",
    "game-changer",
    "unleash",
    "supercharge",
    "transformative",
    "next-gen",
    "cutting-edge",
    "seamless",
    "unlock",
    "ai-powered productivity app",
}

REQUIRED_THEMES = {
    "decision",
    "noise",
    "priority",
    "action",
}

PRODUCT_ANCHORS = {
    "3 priorities",
    "ignored signals",
    "why",
    "next action",
    "decision system",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quality checks on generated drafts.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero exit code when any draft fails quality checks.",
    )
    return parser.parse_args()


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def load_drafts() -> dict[str, str]:
    if not DRAFTS_DIR.exists():
        raise FileNotFoundError(f"{DRAFTS_DIR} does not exist")

    drafts: dict[str, str] = {}
    for channel in ("x", "linkedin", "blog"):
        path = DRAFTS_DIR / f"latest-{channel}.md"
        if path.exists():
            drafts[path.name] = path.read_text(encoding="utf-8")
    return drafts


def text_hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def analyse_text(text: str, previous_hashes: set[str]) -> dict[str, Any]:
    text_lower = text.lower()
    banned_hits = [phrase for phrase in BANNED_PHRASES if phrase in text_lower]
    required_hits = [theme for theme in REQUIRED_THEMES if theme in text_lower]
    anchor_hits = [anchor for anchor in PRODUCT_ANCHORS if anchor in text_lower]

    sentence_count = max(1, len([x for x in re.split(r"[.!?]+", text) if x.strip()]))
    word_count = len(re.findall(r"[a-zA-Z0-9]+", text))

    current_hash = text_hash(text)
    repeated_hash = current_hash in previous_hashes

    score = 100
    score -= len(banned_hits) * 20
    if len(required_hits) < 2:
        score -= 25
    if len(anchor_hits) < 2:
        score -= 25
    if repeated_hash:
        score -= 30
    if word_count < 25:
        score -= 20
    if word_count > 260:
        score -= 10

    passed = score >= 70 and not banned_hits and len(anchor_hits) >= 2

    return {
        "passed": passed,
        "score": score,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "banned_hits": banned_hits,
        "required_hits": required_hits,
        "anchor_hits": anchor_hits,
        "repeated_hash": repeated_hash,
        "hash": current_hash,
    }


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    memory = load_json(MEMORY_PATH, default={"angles": [], "hashes": []})
    previous_hashes = set(memory.get("hashes", []))

    drafts = load_drafts()
    manifest = load_json(MANIFEST_PATH, default={})
    plan = manifest.get("plan", {})

    report: dict[str, Any] = {}
    skipped: list[str] = []

    if bool(plan.get("skip_generation")):
        skipped.append("planner_skip_generation")

    if not drafts:
        skipped.append("no_latest_drafts")

    for filename, text in drafts.items():
        report[filename] = analyse_text(text, previous_hashes)

    totals = {
        "drafts": len(report),
        "passed": sum(1 for item in report.values() if item.get("passed")),
    }
    totals["failed"] = totals["drafts"] - totals["passed"]

    overall_passed = totals["drafts"] > 0 and totals["failed"] == 0 and not skipped

    payload = {
        "summary": {
            **totals,
            "skipped": skipped,
            "overall_passed": overall_passed,
        },
        "plan": plan,
        "report": report,
    }

    out = OUTPUT_DIR / "quality_report.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))

    if args.strict and not overall_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
