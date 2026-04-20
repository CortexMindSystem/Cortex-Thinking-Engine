"""Tests for SimpliXio automation orchestration and quality guardrails."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOMATION_ROOT = REPO_ROOT / "cortexos_automation_scripts"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


pipeline_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "run_weekly_pipeline.py",
    "run_weekly_pipeline_module",
)
quality_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "marketing_quality_gate.py",
    "marketing_quality_gate_module",
)
marketing_mod = load_module(
    AUTOMATION_ROOT / "marketing_automation.py",
    "marketing_automation_module",
)
marketing_mod.CortexBrief.model_rebuild(_types_namespace={"Priority": marketing_mod.Priority})
marketing_mod.WeeklyReview.model_rebuild(_types_namespace={"Any": Any})
marketing_mod.Config.model_rebuild(_types_namespace={"Path": Path})


def test_pipeline_step_order():
    steps = pipeline_mod.build_steps(strict_quality=False)
    names = [name for name, _cmd, _strict in steps]
    assert names == [
        "Filter signals",
        "Build SimpliXio Today artifact",
        "Build weekly review",
        "Generate marketing content",
        "Run marketing quality gate",
        "Publish outputs",
    ]


def test_pipeline_strict_quality_flag():
    steps = pipeline_mod.build_steps(strict_quality=True)
    quality = [step for step in steps if step[0] == "Run marketing quality gate"][0]
    _name, cmd, fail_on_error = quality
    assert "--strict" in cmd
    assert fail_on_error is True


def test_quality_gate_detects_repeated_hash():
    analysis = quality_mod.analyse_text(
        "Decision system with 3 priorities. Why and next action. Ignored signals.",
        previous_hashes={quality_mod.text_hash("Decision system with 3 priorities. Why and next action. Ignored signals.")},
    )
    assert analysis["repeated_hash"] is True
    assert analysis["passed"] is True or analysis["score"] < 100


def test_content_plan_skips_when_no_signal():
    brief = marketing_mod.CortexBrief(date="2026-04-19", priorities=[], ignored_signals_count=0)
    weekly = marketing_mod.WeeklyReview(days_covered=0, top_priorities=[], recommendations=[])
    plan = marketing_mod.choose_content_plan(brief, weekly, memory={"angles": [], "hashes": []})
    assert plan.skip_generation is True
    assert plan.angle == "insufficient_signal"


def test_content_plan_avoids_recent_angle():
    brief = marketing_mod.CortexBrief(
        date="2026-04-19",
        priorities=[marketing_mod.Priority(title="Ship release", why="Users need stability", action="Publish build")],
        ignored_signals_count=4,
    )
    weekly = marketing_mod.WeeklyReview(days_covered=0, top_priorities=[], recommendations=[])
    plan = marketing_mod.choose_content_plan(
        brief,
        weekly,
        memory={"angles": [{"angle": "today_priority"}], "hashes": []},
    )
    assert plan.angle == "ignored_signals"


def test_generated_copy_uses_simplixio_branding():
    cfg = marketing_mod.Config()
    brief = marketing_mod.CortexBrief(
        date="2026-04-19",
        priorities=[
            marketing_mod.Priority(
                title="Strengthen offline queue",
                why="Reliability during travel",
                action="Sync when online resumes",
            )
        ],
        ignored_signals_count=3,
    )
    weekly = marketing_mod.WeeklyReview(days_covered=4)
    plan = marketing_mod.ContentPlan(
        angle="today_priority",
        score=4,
        reason="Daily top priority exists with why/action context.",
        title="Top priority angle",
    )
    posts = marketing_mod.deterministic_posts(cfg, brief, weekly, trends=[], plan=plan)
    assert posts
    assert all("SimpliXio" in post.body for post in posts.values())
    assert all("CortexOS today" not in post.body for post in posts.values())
