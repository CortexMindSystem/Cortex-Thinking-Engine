#!/usr/bin/env python3
"""Publish SimpliXio generated posts safely after quality passes.

Dry-run by default. Real publishing requires explicit env flags.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
QUALITY_REPORT_PATH = AUTOMATION_ROOT / "output" / "quality_gate" / "quality_report.json"
MANIFEST_PATH = AUTOMATION_ROOT / "output" / "publish" / "latest_posts.json"
MEMORY_PATH = AUTOMATION_ROOT / "output" / "memory" / "content_memory.json"
OUTPUT_DIR = AUTOMATION_ROOT / "output" / "publish"


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def should_publish() -> tuple[bool, list[str]]:
    reasons: list[str] = []

    dry_run = os.getenv("PUBLISH_DRY_RUN", "true").lower() == "true"
    if dry_run:
        reasons.append("publish_dry_run_enabled")

    quality = load_json(QUALITY_REPORT_PATH, default={})
    overall_passed = bool(quality.get("summary", {}).get("overall_passed", False))
    if not overall_passed:
        reasons.append("quality_gate_failed")

    manifest = load_json(MANIFEST_PATH, default={})
    if not manifest.get("posts"):
        reasons.append("no_posts_in_manifest")

    return (len(reasons) == 0), reasons


def append_memory(manifest: dict[str, Any]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    memory = load_json(MEMORY_PATH, default={"angles": [], "hashes": []})

    plan = manifest.get("plan", {})
    angle = str(plan.get("angle", "")).strip()

    post_hashes = [
        str(item.get("hash", "")).strip()
        for item in manifest.get("posts", {}).values()
        if str(item.get("hash", "")).strip()
    ]

    if angle:
        memory.setdefault("angles", []).append(
            {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "angle": angle,
                "title": str(plan.get("title", "")),
            }
        )
        memory["angles"] = memory["angles"][-30:]

    memory.setdefault("hashes", [])
    for post_hash in post_hashes:
        if post_hash not in memory["hashes"]:
            memory["hashes"].append(post_hash)
    memory["hashes"] = memory["hashes"][-200:]

    MEMORY_PATH.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def publish_stub_results(manifest: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}

    publish_x = os.getenv("PUBLISH_X", "false").lower() == "true"
    publish_linkedin = os.getenv("PUBLISH_LINKEDIN", "false").lower() == "true"

    x_post = manifest.get("posts", {}).get("x")
    linkedin_post = manifest.get("posts", {}).get("linkedin")

    if publish_x and x_post:
        results["x"] = {
            "status": "ready",
            "reason": "X publishing is enabled but API publishing is intentionally externalized.",
            "text": x_post.get("body", "")[:280],
        }
    else:
        results["x"] = {"status": "skipped", "reason": "PUBLISH_X disabled or missing x post."}

    if publish_linkedin and linkedin_post:
        results["linkedin"] = {
            "status": "ready",
            "reason": "LinkedIn publishing is enabled but API publishing is intentionally externalized.",
            "text": linkedin_post.get("body", ""),
        }
    else:
        results["linkedin"] = {"status": "skipped", "reason": "PUBLISH_LINKEDIN disabled or missing linkedin post."}

    return results


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_json(MANIFEST_PATH, default={})
    can_publish, reasons = should_publish()

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "can_publish": can_publish,
        "reasons": reasons,
        "results": {},
    }

    if can_publish:
        payload["results"] = publish_stub_results(manifest)
        append_memory(manifest)
        payload["status"] = "passed"
    else:
        payload["status"] = "skipped"

    output_path = OUTPUT_DIR / "latest_publish.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
