"""Tests for Decision Engine and DecisionEngine."""

import pytest
from pathlib import Path

from cortex_core.decisions import (
    Decision,
    DecisionEngine,
    DailyDecisionBrief,
    Priority,
)
from cortex_core.scoring import ArticleScore


class TestPriority:
    def test_create_priority(self):
        p = Priority(rank=1, title="Test priority", why_it_matters="because", next_step="do it")
        assert p.rank == 1
        assert p.relevance_score == 0.0

    def test_to_dict(self):
        p = Priority(rank=1, title="Test", why_it_matters="reason", next_step="step", source="manual")
        d = p.to_dict()
        assert d["rank"] == 1
        assert d["source"] == "manual"


class TestDecision:
    def test_create_decision(self):
        d = Decision(decision="Ship v2", reason="Tested", project="CortexOS")
        assert d.decision == "Ship v2"
        assert d.outcome == ""

    def test_to_dict(self):
        d = Decision(decision="Ship v2", reason="Tested", project="CortexOS")
        data = d.to_dict()
        assert data["decision"] == "Ship v2"
        assert "created_at" in data


class TestDecisionEngine:
    @pytest.fixture()
    def engine(self, tmp_path):
        return DecisionEngine(data_dir=tmp_path)

    def test_generate_brief_empty(self, engine):
        brief = engine.generate_brief(scored_items=[], insights=[], signals=[])
        assert isinstance(brief, DailyDecisionBrief)
        assert len(brief.priorities) == 0

    def test_generate_brief_with_items(self, engine):
        items = [
            ArticleScore(
                title="New AI Agent Framework",
                ai_related=True,
                high_signal=True,
                context_overlap=0.5,
                noise=False,
                composite_score=0.85,
                ai_relevance=0.8,
                project_relevance=0.7,
                novelty=0.9,
                actionability=0.7,
            ),
        ]
        brief = engine.generate_brief(scored_items=items, insights=[], signals=[])
        assert len(brief.priorities) >= 1

    def test_brief_limits_priorities(self, engine):
        items = [
            ArticleScore(
                title=f"Item {i}",
                ai_related=True,
                high_signal=True,
                context_overlap=0.5,
                noise=False,
                composite_score=0.5 + i * 0.01,
                ai_relevance=0.5,
                project_relevance=0.5,
                novelty=0.5,
                actionability=0.5,
            )
            for i in range(20)
        ]
        brief = engine.generate_brief(scored_items=items, insights=[], signals=[])
        assert len(brief.priorities) <= 7

    def test_record_decision(self, engine):
        d = engine.record_decision(
            decision="Ship v2",
            reason="All tests pass",
            project="CortexOS",
        )
        assert isinstance(d, Decision)
        assert len(engine.decisions) == 1

    def test_record_outcome(self, engine):
        d = engine.record_decision(decision="Ship", reason="Ready", project="CortexOS")
        engine.record_outcome(d.id, outcome="Shipped successfully", impact_score=0.9)
        updated = engine.decisions[0]
        assert updated.outcome == "Shipped successfully"
        assert updated.impact_score == 0.9

    def test_decision_effectiveness(self, engine):
        d = engine.record_decision(decision="Ship", reason="Ready", project="CortexOS")
        engine.record_outcome(d.id, outcome="Success", impact_score=0.8)
        eff = engine.decision_effectiveness()
        assert eff["total_decisions"] == 1
        assert eff["evaluated_decisions"] == 1
        assert eff["average_impact"] == 0.8

    def test_persistence(self, engine, tmp_path):
        engine.record_decision(decision="Test", reason="Testing", project="test")
        engine2 = DecisionEngine(storage_dir=tmp_path)
        assert len(engine2.decisions) == 1

    def test_brief_to_dict(self, engine):
        brief = engine.generate_brief(scored_items=[], insights=[], signals=[])
        d = brief.to_dict()
        assert "date" in d
        assert "priorities" in d
        assert "ignored" in d

    def test_save_and_load_brief(self, engine):
        brief = engine.generate_brief(scored_items=[], insights=[], signals=[])
        engine.save_brief(brief)
        loaded = engine.load_latest_brief()
        assert loaded is not None
        assert loaded["date"] == brief.date
