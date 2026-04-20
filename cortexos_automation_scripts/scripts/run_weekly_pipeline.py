#!/usr/bin/env python3
"""Run the SimpliXio weekly automation pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = AUTOMATION_ROOT / "output" / "logs"
SUMMARY_DIR = AUTOMATION_ROOT / "output" / "summaries"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SimpliXio weekly automation pipeline.")
    parser.add_argument(
        "--strict-quality",
        action="store_true",
        help="Fail the pipeline if quality gate finds failed drafts.",
    )
    return parser.parse_args()


def detect_python() -> str:
    candidates = [
        AUTOMATION_ROOT / ".venv" / "bin" / "python",
        AUTOMATION_ROOT.parent / ".venv" / "bin" / "python",
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return "python3"


def build_steps(strict_quality: bool) -> list[tuple[str, list[str], bool]]:
    python_bin = detect_python()

    quality_cmd = [python_bin, "scripts/marketing_quality_gate.py"]
    if strict_quality:
        quality_cmd.append("--strict")

    # (name, command, fail_pipeline_on_error)
    return [
        ("Filter signals", [python_bin, "scripts/filter_signals.py"], True),
        ("Build SimpliXio Today artifact", [python_bin, "scripts/build_cortex_today.py"], True),
        ("Build weekly review", [python_bin, "scripts/build_weekly_review.py"], True),
        ("Generate marketing content", [python_bin, "marketing_automation.py"], True),
        ("Run marketing quality gate", quality_cmd, strict_quality),
        ("Publish outputs", [python_bin, "scripts/publish_outputs.py"], False),
    ]


def run_step(name: str, command: list[str]) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=AUTOMATION_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "command": command,
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def parse_json_output(step_result: dict[str, Any]) -> dict[str, Any] | None:
    stdout = str(step_result.get("stdout", "")).strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def write_markdown_summary(payload: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append(f"# SimpliXio Automation Summary · {payload['generated_at']}")
    lines.append("")
    lines.append(f"- Strict quality: `{str(payload['strict_quality']).lower()}`")
    lines.append(f"- Failed: `{str(payload['failed']).lower()}`")
    lines.append(f"- Steps completed: `{len(payload['steps'])}`")
    lines.append("")
    lines.append("## Step Results")
    lines.append("")

    for step in payload["steps"]:
        status = "passed" if step["returncode"] == 0 else "failed"
        lines.append(f"- **{step['name']}**: {status}")
        if step.get("skip_reason"):
            lines.append(f"  - skip reason: {step['skip_reason']}")

    skipped = payload.get("skipped", [])
    if skipped:
        lines.append("")
        lines.append("## Skipped")
        lines.append("")
        for item in skipped:
            lines.append(f"- {item}")

    lines.append("")
    lines.append("## Logs")
    lines.append("")
    lines.append(f"- JSON: `{payload['log_path']}`")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    steps = build_steps(strict_quality=args.strict_quality)

    results: list[dict[str, Any]] = []
    skipped: list[str] = []
    failed = False

    for name, command, fail_pipeline_on_error in steps:
        result = run_step(name, command)
        parsed = parse_json_output(result)

        if parsed and name == "Publish outputs" and parsed.get("status") == "skipped":
            skip_reasons = parsed.get("reasons", [])
            if skip_reasons:
                result["skip_reason"] = ",".join(skip_reasons)
                skipped.extend([f"publish:{reason}" for reason in skip_reasons])

        results.append(result)

        if result["returncode"] != 0 and fail_pipeline_on_error:
            failed = True
            break

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"weekly-pipeline-{stamp}.json"
    summary_path = SUMMARY_DIR / f"weekly-pipeline-{stamp}.md"

    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "failed": failed,
        "strict_quality": args.strict_quality,
        "steps": results,
        "skipped": skipped,
        "log_path": str(log_path),
        "summary_path": str(summary_path),
    }

    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown_summary(payload, summary_path)

    print(
        json.dumps(
            {
                "failed": failed,
                "log": str(log_path),
                "summary": str(summary_path),
                "steps_completed": len(results),
            },
            indent=2,
        )
    )

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
