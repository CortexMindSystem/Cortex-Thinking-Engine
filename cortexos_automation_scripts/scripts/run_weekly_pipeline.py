#!/usr/bin/env python3
"""Run the CortexOS automation weekly pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = AUTOMATION_ROOT / "output" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CortexOS weekly automation pipeline.")
    parser.add_argument(
        "--strict-quality",
        action="store_true",
        help="Fail the pipeline if quality gate finds failed drafts.",
    )
    return parser.parse_args()


def build_steps(strict_quality: bool) -> list[tuple[str, list[str]]]:
    python_bin = detect_python()
    quality_cmd = [python_bin, "scripts/marketing_quality_gate.py"]
    if strict_quality:
        quality_cmd.append("--strict")

    return [
        ("Filter signals", [python_bin, "scripts/filter_signals.py"]),
        ("Build CortexOS Today artifact", [python_bin, "scripts/build_cortex_today.py"]),
        ("Run marketing automation", [python_bin, "marketing_automation.py"]),
        ("Run marketing quality gate", quality_cmd),
        ("Build weekly review", [python_bin, "scripts/build_weekly_review.py"]),
    ]


def detect_python() -> str:
    candidates = [
        AUTOMATION_ROOT / ".venv" / "bin" / "python",
        AUTOMATION_ROOT.parent / ".venv" / "bin" / "python",
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return "python3"


def run_step(name: str, command: list[str]) -> dict:
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


def main() -> None:
    args = parse_args()
    steps = build_steps(strict_quality=args.strict_quality)

    results: list[dict] = []
    failed = False

    for name, command in steps:
        result = run_step(name, command)
        results.append(result)
        if result["returncode"] != 0:
            failed = True
            break

    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "failed": failed,
        "strict_quality": args.strict_quality,
        "steps": results,
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"weekly-pipeline-{stamp}.json"
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "failed": failed,
                "log": str(log_path),
                "steps_completed": len(results),
            },
            indent=2,
        )
    )

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
