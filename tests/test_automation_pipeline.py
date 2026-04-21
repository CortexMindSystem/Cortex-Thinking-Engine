"""Tests for SimpliXio automation orchestration and quality guardrails."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any
import importlib


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOMATION_ROOT = REPO_ROOT / "cortexos_automation_scripts"
AUTOMATION_SCRIPTS = AUTOMATION_ROOT / "scripts"

if str(AUTOMATION_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_SCRIPTS))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


pipeline_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "run_weekly_pipeline.py",
    "run_weekly_pipeline_module",
)
acq_pipeline_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "run_acquisition_pipeline.py",
    "run_acquisition_pipeline_module",
)
quality_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "marketing_quality_gate.py",
    "marketing_quality_gate_module",
)
acq_quality_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "acquisition_quality_gate.py",
    "acquisition_quality_gate_module",
)
outreach_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "outreach_drafter.py",
    "outreach_drafter_module",
)
acq_crm_mod = importlib.import_module("acquisition_crm")
lead_scorer_mod = load_module(
    AUTOMATION_ROOT / "scripts" / "lead_scorer.py",
    "lead_scorer_module",
)
marketing_mod = load_module(
    AUTOMATION_ROOT / "marketing_automation.py",
    "marketing_automation_module",
)
marketing_mod.CortexBrief.model_rebuild(_types_namespace={"Priority": marketing_mod.Priority})
marketing_mod.WeeklyReview.model_rebuild(_types_namespace={"Any": Any})
marketing_mod.DecisionReplay.model_rebuild(_types_namespace={"Any": Any})
marketing_mod.Config.model_rebuild(_types_namespace={"Path": Path})


def test_pipeline_step_order():
    steps = pipeline_mod.build_steps(strict_quality=False)
    names = [name for name, _cmd, _strict in steps]
    assert names == [
        "Filter signals",
        "Build SimpliXio Today artifact",
        "Build weekly review",
        "Build decision replay",
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


def test_acquisition_pipeline_step_order():
    steps = acq_pipeline_mod.build_daily_steps(strict_quality=False)
    names = [name for name, _cmd, _strict in steps]
    assert names == [
        "Collect lead signals",
        "Score leads",
        "Draft outreach",
        "Generate public content",
        "Run acquisition quality gate",
    ]


def test_acquisition_pipeline_strict_quality_flag():
    steps = acq_pipeline_mod.build_daily_steps(strict_quality=True)
    quality = [step for step in steps if step[0] == "Run acquisition quality gate"][0]
    _name, cmd, fail_on_error = quality
    assert "--strict" in cmd
    assert fail_on_error is True


def test_acquisition_quality_gate_detects_hype_phrase():
    result = acq_quality_mod.analyse_text(
        "This revolutionary AI-powered productivity app will supercharge everything."
    )
    assert result.passed is False
    assert result.score < 70


def test_lead_scorer_boosts_high_signal_github_repos():
    score, reason = lead_scorer_mod.score_lead(
        "Founder shipping decision system for builders",
        "github",
        {
            "excerpt": "We ship weekly and focus on prioritization and context.",
            "tags": ["open source", "workflow"],
            "raw": {"stars": 800, "forks": 120, "updated_at": "2026-04-20T00:00:00Z"},
        },
    )
    assert score >= 55
    assert "github:high_stars" in reason or "founder" in reason


def test_lead_scorer_penalizes_internal_artifacts():
    score, _reason = lead_scorer_mod.score_lead(
        "Internal weekly review",
        "simplixio_weekly_review",
        {"excerpt": "internal artifact", "tags": ["internal_artifact"], "raw": {}},
    )
    assert score <= 20


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
    replay = marketing_mod.DecisionReplay()
    plan = marketing_mod.choose_content_plan(brief, weekly, replay, memory={"angles": [], "hashes": []})
    assert plan.skip_generation is True
    assert plan.angle == "insufficient_signal"


def test_content_plan_avoids_recent_angle():
    brief = marketing_mod.CortexBrief(
        date="2026-04-19",
        priorities=[marketing_mod.Priority(title="Ship release", why="Users need stability", action="Publish build")],
        ignored_signals_count=4,
    )
    weekly = marketing_mod.WeeklyReview(days_covered=0, top_priorities=[], recommendations=[])
    replay = marketing_mod.DecisionReplay()
    plan = marketing_mod.choose_content_plan(
        brief,
        weekly,
        replay,
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
    replay = marketing_mod.DecisionReplay(
        date="2026-04-19",
        signals_reviewed=20,
        signals_kept=6,
        signals_ignored=14,
        summary="SimpliXio reduced 20 signals into 3 priorities.",
    )
    plan = marketing_mod.ContentPlan(
        angle="today_priority",
        score=4,
        reason="Daily top priority exists with why/action context.",
        title="Top priority angle",
    )
    posts = marketing_mod.deterministic_posts(cfg, brief, weekly, replay, trends=[], plan=plan)
    assert posts
    assert all("SimpliXio" in post.body for post in posts.values())
    assert all("CortexOS today" not in post.body for post in posts.values())


def test_content_plan_prefers_decision_replay_signal():
    brief = marketing_mod.CortexBrief(
        date="2026-04-19",
        priorities=[],
        ignored_signals_count=0,
    )
    weekly = marketing_mod.WeeklyReview(days_covered=0, top_priorities=[], recommendations=[])
    replay = marketing_mod.DecisionReplay(signals_reviewed=30, signals_kept=8, signals_ignored=22)
    plan = marketing_mod.choose_content_plan(brief, weekly, replay, memory={"angles": [], "hashes": []})
    assert plan.angle == "decision_replay_proof"


def test_outreach_drafts_only_fit_leads(tmp_path):
    db_path = tmp_path / "acq.sqlite3"
    output_dir = tmp_path / "output"
    acq_crm_mod.DB_PATH = db_path
    acq_crm_mod.OUTPUT_DIR = output_dir
    outreach_mod.OUTPUT_DIR = output_dir
    acq_quality_mod.OUTPUT_DIR = output_dir

    conn = acq_crm_mod.connect()
    acq_crm_mod.init_db(conn)

    fit_id = acq_crm_mod.upsert_lead(
        conn,
        source="github",
        source_url="https://github.com/example/fit",
        title="Founder shipping prioritization workflows",
        pain_signal="Decision fatigue",
        raw_payload={"excerpt": "strong fit"},
    )
    candidate_id = acq_crm_mod.upsert_lead(
        conn,
        source="github",
        source_url="https://github.com/example/candidate",
        title="Interesting but weaker match",
        pain_signal="Unknown",
        raw_payload={"excerpt": "candidate"},
    )
    acq_crm_mod.update_lead_score(
        conn,
        lead_id=fit_id,
        fit_score=82,
        pain_signal="Decision fatigue",
        status="fit",
        next_action="draft_outreach",
    )
    acq_crm_mod.update_lead_score(
        conn,
        lead_id=candidate_id,
        fit_score=50,
        pain_signal="Unknown",
        status="candidate",
        next_action="manual_review",
    )

    result = outreach_mod.run(limit=20)
    assert result["created"] == 1
    assert result["from_fit"] == 1
    assert result["from_candidate"] == 0


def test_acquisition_quality_gate_rejects_non_fit_outreach(tmp_path):
    db_path = tmp_path / "acq.sqlite3"
    output_dir = tmp_path / "output"
    acq_crm_mod.DB_PATH = db_path
    acq_crm_mod.OUTPUT_DIR = output_dir
    acq_quality_mod.OUTPUT_DIR = output_dir

    conn = acq_crm_mod.connect()
    acq_crm_mod.init_db(conn)

    lead_id = acq_crm_mod.upsert_lead(
        conn,
        source="rss",
        source_url="https://example.com/low-fit",
        title="Low-fit generic content",
        pain_signal="Unknown",
        raw_payload={"excerpt": "generic"},
    )
    acq_crm_mod.update_lead_score(
        conn,
        lead_id=lead_id,
        fit_score=34,
        pain_signal="Unknown",
        status="candidate",
        next_action="manual_review",
    )
    acq_crm_mod.insert_message(
        conn,
        lead_id=lead_id,
        channel="private_outreach",
        message_type="private",
        draft_text="Hi, https://example.com/low-fit looked relevant for decision system workflows.",
        status="needs_approval",
    )

    result = acq_quality_mod.run(strict=False)
    assert result["failed_count"] >= 1
    assert any(item["status"] == "rejected_quality" for item in result["messages"])


def test_scoring_queue_includes_existing_fit_leads(tmp_path):
    db_path = tmp_path / "acq.sqlite3"
    output_dir = tmp_path / "output"
    acq_crm_mod.DB_PATH = db_path
    acq_crm_mod.OUTPUT_DIR = output_dir

    conn = acq_crm_mod.connect()
    acq_crm_mod.init_db(conn)
    lead_id = acq_crm_mod.upsert_lead(
        conn,
        source="github",
        source_url="https://github.com/example/re-score",
        title="Founder building decision workflows",
        pain_signal="Decision fatigue",
        raw_payload={"excerpt": "active project"},
    )
    acq_crm_mod.update_lead_score(
        conn,
        lead_id=lead_id,
        fit_score=78,
        pain_signal="Decision fatigue",
        status="fit",
        next_action="draft_outreach",
    )

    queue = acq_crm_mod.list_leads_for_scoring(conn, limit=10)
    assert any(item.id == lead_id for item in queue)
