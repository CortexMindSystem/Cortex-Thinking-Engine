#!/usr/bin/env python3
"""Run SimpliXio acquisition pipeline (daily or weekly mode)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from acquisition_crm import OUTPUT_DIR, connect, init_db, insert_run


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = OUTPUT_DIR / "logs"
SUMMARY_DIR = OUTPUT_DIR / "summaries"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SimpliXio acquisition automation pipeline.")
    parser.add_argument("--mode", choices=["daily", "weekly"], default="daily")
    parser.add_argument("--strict-quality", action="store_true")
    return parser.parse_args()


def detect_python() -> str:
    candidates = [
        AUTOMATION_ROOT / ".venv" / "bin" / "python",
        AUTOMATION_ROOT.parent / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "python3"


def build_daily_steps(strict_quality: bool) -> list[tuple[str, list[str], bool]]:
    py = detect_python()
    quality_cmd = [py, "scripts/acquisition_quality_gate.py"]
    if strict_quality:
        quality_cmd.append("--strict")
    return [
        ("Collect lead signals", [py, "scripts/lead_collector.py"], True),
        ("Score leads", [py, "scripts/lead_scorer.py"], True),
        ("Draft outreach", [py, "scripts/outreach_drafter.py"], True),
        ("Generate public content", [py, "scripts/content_engine.py"], True),
        ("Run acquisition quality gate", quality_cmd, strict_quality),
    ]


def build_weekly_steps() -> list[tuple[str, list[str], bool]]:
    py = detect_python()
    return [
        ("Collect lead signals", [py, "scripts/lead_collector.py"], True),
        ("Score leads", [py, "scripts/lead_scorer.py"], True),
    ]


def run_step(name: str, command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=AUTOMATION_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def parse_json_output(step_result: dict[str, Any]) -> dict[str, Any] | None:
    stdout = str(step_result.get("stdout", "")).strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def weekly_internal_summary() -> dict[str, Any]:
    conn = connect()
    init_db(conn)

    top_leads = conn.execute(
        """
        SELECT source, title, source_url, fit_score, pain_signal
        FROM leads
        WHERE status = 'fit'
        ORDER BY fit_score DESC, id DESC
        LIMIT 20
        """
    ).fetchall()
    top_content = conn.execute(
        """
        SELECT angle, channel, status, quality_score, created_at
        FROM content
        ORDER BY id DESC
        LIMIT 40
        """
    ).fetchall()

    angle_counts: dict[str, int] = {}
    for row in top_content:
        angle = str(row["angle"])
        angle_counts[angle] = angle_counts.get(angle, 0) + 1

    recommendations: list[str] = []
    if top_leads:
        recommendations.append("Prioritize high-fit leads with clear decision-fatigue or prioritisation pain.")
    if angle_counts:
        best_angle = sorted(angle_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
        recommendations.append(f"Keep testing angle '{best_angle}' but rotate weekly to avoid repetition.")
    recommendations.append("Keep private outreach in needs_approval until explicit approval workflow is set.")

    summary = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fit_leads_count": len(top_leads),
        "top_leads": [dict(row) for row in top_leads[:10]],
        "content_angle_counts": angle_counts,
        "recommendations": recommendations,
    }
    return summary


def write_markdown_summary(mode: str, payload: dict[str, Any], path: Path) -> None:
    lines: list[str] = [
        f"# SimpliXio Acquisition {mode.title()} Summary",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Failed: `{str(payload.get('failed', False)).lower()}`",
        "",
    ]

    if mode == "daily":
        lines.append("## Step Results")
        lines.append("")
        for step in payload.get("steps", []):
            status = "passed" if step["returncode"] == 0 else "failed"
            lines.append(f"- **{step['name']}**: {status}")
            if step.get("skip_reason"):
                lines.append(f"  - skip reason: {step['skip_reason']}")
    else:
        lines.append("## Weekly Signals")
        lines.append("")
        lines.append(f"- Fit leads: `{payload.get('fit_leads_count', 0)}`")
        for item in payload.get("recommendations", []):
            lines.append(f"- {item}")

    skipped = payload.get("skipped", [])
    if skipped:
        lines.append("")
        lines.append("## Skipped")
        lines.append("")
        for item in skipped:
            lines.append(f"- {item}")

    path.write_text("\n".join(lines), encoding="utf-8")


def run_daily(strict_quality: bool) -> dict[str, Any]:
    steps = build_daily_steps(strict_quality)
    results: list[dict[str, Any]] = []
    skipped: list[str] = []
    failed = False

    for name, command, fail_on_error in steps:
        result = run_step(name, command)
        parsed = parse_json_output(result)
        if parsed and name == "Run acquisition quality gate" and int(parsed.get("failed_count", 0)) > 0 and not strict_quality:
            result["skip_reason"] = "quality_rejections_marked_for_manual_review"
            skipped.append(f"quality_rejected:{parsed.get('failed_count')}")
        results.append(result)
        if result["returncode"] != 0 and fail_on_error:
            failed = True
            break

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "failed": failed,
        "mode": "daily",
        "strict_quality": strict_quality,
        "steps": results,
        "skipped": skipped,
    }


def run_weekly() -> dict[str, Any]:
    steps = build_weekly_steps()
    results: list[dict[str, Any]] = []
    failed = False

    for name, command, fail_on_error in steps:
        result = run_step(name, command)
        results.append(result)
        if result["returncode"] != 0 and fail_on_error:
            failed = True
            break

    summary = weekly_internal_summary()
    summary["mode"] = "weekly"
    summary["failed"] = failed
    summary["steps"] = results
    return summary


def main() -> None:
    args = parse_args()
    if args.mode == "daily":
        payload = run_daily(args.strict_quality)
    else:
        payload = run_weekly()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"acquisition-{args.mode}-{stamp}.json"
    summary_path = SUMMARY_DIR / f"acquisition-{args.mode}-{stamp}.md"
    payload["log_path"] = str(log_path)
    payload["summary_path"] = str(summary_path)

    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown_summary(args.mode, payload, summary_path)

    conn = connect()
    init_db(conn)
    insert_run(
        conn,
        pipeline="acquisition",
        mode=args.mode,
        status="failed" if payload.get("failed") else "ok",
        summary_json=payload,
        summary_path=str(summary_path),
    )

    print(
        json.dumps(
            {
                "failed": bool(payload.get("failed")),
                "mode": args.mode,
                "log": str(log_path),
                "summary": str(summary_path),
            },
            indent=2,
        )
    )
    if payload.get("failed"):
        sys.exit(1)


if __name__ == "__main__":
    main()
