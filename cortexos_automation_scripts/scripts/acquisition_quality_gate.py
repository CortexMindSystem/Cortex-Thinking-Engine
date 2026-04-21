#!/usr/bin/env python3
"""Quality and compliance gate for acquisition drafts and public content."""

from __future__ import annotations

import json
import os
import re
import sys
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from acquisition_crm import (
    AUTOMATION_ROOT,
    OUTPUT_DIR,
    connect,
    init_db,
    update_content_quality,
    update_message_quality,
)


BANNED = {
    "revolutionary",
    "game-changer",
    "unleash",
    "supercharge",
    "cutting-edge",
    "ai-powered productivity app",
    "seamless",
    "fake urgency",
}

ANCHORS = {
    "decision system",
    "noise",
    "3 priorities",
    "ignored signals",
    "what matters",
    "why",
    "what to do next",
}


@dataclass
class GateResult:
    score: int
    passed: bool
    reason: str


def analyse_text(text: str) -> GateResult:
    lower = text.lower()
    banned_hits = [x for x in BANNED if x in lower]
    anchors = [x for x in ANCHORS if x in lower]
    words = len(re.findall(r"[a-zA-Z0-9]+", text))

    score = 100
    if banned_hits:
        score -= 25 * len(banned_hits)
    if len(anchors) < 2:
        score -= 30
    if words < 20:
        score -= 20
    if "http://" in lower or "https://" in lower:
        score += 2  # slight reward for concrete reference
    score = max(0, min(score, 100))

    passed = score >= 70 and not banned_hits
    reason = "ok" if passed else f"banned={len(banned_hits)},anchors={len(anchors)},words={words}"
    return GateResult(score=score, passed=passed, reason=reason)


def run(*, strict: bool = False) -> dict[str, Any]:
    load_dotenv(AUTOMATION_ROOT / ".env")
    env_strict = os.getenv("ACQ_STRICT", "false").lower() == "true"
    publish_public = os.getenv("PUBLISH_PUBLIC", "false").lower() == "true"

    conn = connect()
    init_db(conn)

    messages = conn.execute(
        "SELECT id, draft_text, draft_hash, status FROM messages ORDER BY id DESC LIMIT 100"
    ).fetchall()
    content = conn.execute(
        "SELECT id, body, body_hash, status FROM content ORDER BY id DESC LIMIT 100"
    ).fetchall()

    message_report: list[dict[str, Any]] = []
    content_report: list[dict[str, Any]] = []

    failed = 0

    for row in messages:
        text = str(row["draft_text"])
        result = analyse_text(text)
        reason_parts = [result.reason]
        score = result.score
        passed = result.passed

        lower = text.lower()
        if "http://" not in lower and "https://" not in lower and "local://" not in lower:
            score -= 30
            passed = False
            reason_parts.append("missing_specific_reference")
        if "signal i picked up is unknown" in lower:
            score -= 20
            passed = False
            reason_parts.append("missing_specific_reason")
        repeated_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM messages WHERE draft_hash = ?",
                (str(row["draft_hash"]),),
            ).fetchone()[0]
        )
        if repeated_count > 1:
            score -= 25
            passed = False
            reason_parts.append("repeated_message_hash")

        score = max(0, min(score, 100))
        status = "needs_approval"
        if not passed:
            status = "rejected_quality"
            failed += 1
        elif str(row["status"]) != "needs_approval":
            # force safe default for private outbound
            status = "needs_approval"

        update_message_quality(
            conn,
            message_id=int(row["id"]),
            quality_score=score,
            status=status,
            compliance_notes="; ".join(reason_parts) + "; private outbound requires manual approval",
        )
        message_report.append(
            {"id": int(row["id"]), "score": score, "passed": passed, "status": status}
        )

    for row in content:
        text = str(row["body"])
        result = analyse_text(text)
        reason_parts = [result.reason]
        score = result.score
        passed = result.passed

        repeated_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM content WHERE body_hash = ?",
                (str(row["body_hash"]),),
            ).fetchone()[0]
        )
        if repeated_count > 1:
            score -= 25
            passed = False
            reason_parts.append("repeated_content_hash")

        score = max(0, min(score, 100))
        status = "quality_passed"
        if not passed:
            status = "rejected_quality"
            failed += 1
        elif not publish_public:
            status = "ready_for_manual_publish"
        else:
            status = "queued_public"

        update_content_quality(
            conn,
            content_id=int(row["id"]),
            quality_score=score,
            status=status,
            compliance_notes="; ".join(reason_parts),
        )
        content_report.append(
            {"id": int(row["id"]), "score": score, "passed": passed, "status": status}
        )

    payload = {
        "status": "ok" if failed == 0 else "failed",
        "strict": strict,
        "env_strict": env_strict,
        "publish_public": publish_public,
        "failed_count": failed,
        "messages": message_report,
        "content": content_report,
    }

    out_path = OUTPUT_DIR / "quality_report.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run acquisition quality gate.")
    parser.add_argument("--strict", action="store_true", help="Fail when any item fails quality/compliance checks.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run(strict=args.strict)
    print(json.dumps(payload, indent=2))
    if args.strict and payload["failed_count"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
