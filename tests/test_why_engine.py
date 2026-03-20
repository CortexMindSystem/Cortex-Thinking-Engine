"""Tests for the Why Engine — per-item decision intelligence."""

import pytest

from cortex_core.why_engine import (
    DecisionResult,
    EvaluationContext,
    SourceItem,
    WhyEngine,
    _compute_confidence,
    _detect_stance,
    _overlap_ratio,
    _triage,
)

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture()
def engine():
    return WhyEngine()


@pytest.fixture()
def cortex_context():
    """Context of someone building CortexOS."""
    return EvaluationContext(
        goals=["Build CortexOS context engine", "Improve AI systems design"],
        interests=["AI agents", "context memory", "retrieval", "evaluation"],
        current_projects=["CortexOS"],
        ignored_topics=["celebrity news", "entertainment"],
        project_milestones=["Ship Why Engine", "Add hybrid retrieval"],
        project_blockers=["LLM latency on mobile"],
        recent_decisions=["Use rule-based scoring before adding LLM"],
        recent_themes=["context engineering", "agent memory"],
        assumptions=["Rule-based scoring is good enough for v1"],
    )


@pytest.fixture()
def relevant_article():
    return SourceItem(
        title="New AI Agent Memory Framework Released",
        content=(
            "A framework to build persistent context memory for AI agent systems. "
            "The engine supports layered recall and scoring."
        ),
        source_type="article",
        url="https://example.com/agent-memory",
        tags=["ai", "agents"],
    )


@pytest.fixture()
def irrelevant_article():
    return SourceItem(
        title="Celebrity Wedding Photos Go Viral",
        content="Entertainment news about celebrity events.",
        source_type="article",
        tags=["celebrity", "entertainment"],
    )


@pytest.fixture()
def contradicting_article():
    return SourceItem(
        title="Rule-Based AI Scoring Proven Flawed",
        content=(
            "New research shows rule-based scoring is fundamentally flawed "
            "and has been debunked as a viable approach for context engines."
        ),
        source_type="article",
        tags=["ai", "scoring", "evaluation"],
    )


# ── SourceItem tests ────────────────────────────────────────────


class TestSourceItem:
    def test_from_dict(self):
        data = {"title": "Test", "content": "Body", "source_type": "note"}
        item = SourceItem.from_dict(data)
        assert item.title == "Test"
        assert item.source_type == "note"

    def test_to_dict(self):
        item = SourceItem(title="Test", tags=["a"])
        d = item.to_dict()
        assert d["title"] == "Test"
        assert d["tags"] == ["a"]


# ── DecisionResult tests ───────────────────────────────────────


class TestDecisionResult:
    def test_to_dict(self):
        result = DecisionResult(
            summary="Test summary",
            why_it_matters="Important",
            ignore_or_watch="act_now",
            confidence=0.75,
        )
        d = result.to_dict()
        assert d["summary"] == "Test summary"
        assert d["confidence"] == 0.75
        assert d["ignore_or_watch"] == "act_now"
        assert "evaluated_at" in d


# ── Pure helper tests ──────────────────────────────────────────


class TestOverlapRatio:
    def test_full_overlap(self):
        assert _overlap_ratio({"a", "b", "c"}, {"a", "b"}) == 1.0

    def test_no_overlap(self):
        assert _overlap_ratio({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        assert _overlap_ratio({"a", "b", "c"}, {"a", "d"}) == 0.5

    def test_empty_b(self):
        assert _overlap_ratio({"a"}, set()) == 0.0


class TestDetectStance:
    def test_supports_when_high_overlap(self):
        items = {"context", "engine", "memory", "agent"}
        prior = {"context", "engine", "ai"}
        assert _detect_stance(items, prior, "") == "supports"

    def test_contradicts_with_signal_words(self):
        items = {"scoring", "rule", "based", "flawed"}
        prior = {"scoring", "rule"}
        assert _detect_stance(items, prior, "Rule-based scoring is flawed") == "contradicts"

    def test_unclear_when_no_overlap(self):
        items = {"cooking", "recipe"}
        prior = {"ai", "context"}
        assert _detect_stance(items, prior, "A cooking recipe") == "unclear"

    def test_unclear_when_no_prior(self):
        assert _detect_stance({"ai"}, set(), "") == "unclear"


class TestComputeConfidence:
    def test_max_confidence(self):
        c = _compute_confidence(1.0, 1.0, 1.0, 0.0)
        assert c <= 1.0
        assert c >= 0.8

    def test_noise_reduces_confidence(self):
        no_noise = _compute_confidence(0.5, 0.5, 0.5, 0.0)
        with_noise = _compute_confidence(0.5, 0.5, 0.5, 0.5)
        assert with_noise < no_noise

    def test_floor_at_zero(self):
        c = _compute_confidence(0.0, 0.0, 0.0, 1.0)
        assert c == 0.0


class TestTriage:
    def test_act_now_high_confidence(self):
        assert _triage(0.5, 0.0, 0.4, 0.3) == "act_now"

    def test_ignore_noisy(self):
        assert _triage(0.5, 0.5, 0.1, 0.1) == "ignore"

    def test_watch_moderate(self):
        assert _triage(0.15, 0.0, 0.1, 0.1) == "watch"

    def test_ignore_low_everything(self):
        assert _triage(0.05, 0.0, 0.0, 0.0) == "ignore"


# ── WhyEngine integration tests ────────────────────────────────


class TestWhyEngine:
    def test_evaluate_relevant_article(self, engine, cortex_context, relevant_article):
        result = engine.evaluate(relevant_article, cortex_context)
        assert isinstance(result, DecisionResult)
        assert result.ignore_or_watch == "act_now"
        assert result.confidence > 0.1
        assert "ai agents" in result.tags or "ai" in result.tags

    def test_evaluate_irrelevant_article(self, engine, cortex_context, irrelevant_article):
        result = engine.evaluate(irrelevant_article, cortex_context)
        assert result.ignore_or_watch == "ignore"
        assert result.confidence < 0.2

    def test_evaluate_contradicting_article(self, engine, cortex_context, contradicting_article):
        result = engine.evaluate(contradicting_article, cortex_context)
        assert result.contradiction_or_confirmation == "contradicts"

    def test_supports_detection(self, engine, cortex_context):
        item = SourceItem(
            title="Context Engineering Best Practices",
            content="How to build better context memory systems for agents.",
            tags=["context", "agents"],
        )
        result = engine.evaluate(item, cortex_context)
        assert result.contradiction_or_confirmation == "supports"

    def test_summary_from_content(self, engine, cortex_context):
        item = SourceItem(
            title="Test Title",
            content="This is a detailed explanation about something important. More text here.",
        )
        result = engine.evaluate(item, cortex_context)
        assert "detailed explanation" in result.summary

    def test_summary_fallback_to_title(self, engine, cortex_context):
        item = SourceItem(title="Short Title", content="")
        result = engine.evaluate(item, cortex_context)
        assert result.summary == "Short Title"

    def test_project_impact_with_blocker_match(self, engine, cortex_context):
        item = SourceItem(
            title="Reducing LLM Latency on Mobile Devices",
            content="New techniques for reducing LLM latency on mobile.",
            tags=["llm", "mobile"],
        )
        result = engine.evaluate(item, cortex_context)
        impact = result.impact_on_active_project.lower()
        assert "blocker" in impact or "mobile" in impact

    def test_empty_context(self, engine):
        item = SourceItem(title="Anything", content="Some content")
        context = EvaluationContext()
        result = engine.evaluate(item, context)
        assert isinstance(result, DecisionResult)
        assert result.contradiction_or_confirmation == "unclear"

    def test_tags_include_matched_interests(self, engine, cortex_context, relevant_article):
        result = engine.evaluate(relevant_article, cortex_context)
        # Should include at least one item from interests or original tags
        assert len(result.tags) >= 1

    def test_evaluated_at_present(self, engine, cortex_context, relevant_article):
        result = engine.evaluate(relevant_article, cortex_context)
        assert result.evaluated_at  # non-empty ISO timestamp

    def test_recommended_action_for_article(self, engine, cortex_context, relevant_article):
        result = engine.evaluate(relevant_article, cortex_context)
        assert result.recommended_action
        assert len(result.recommended_action) > 10
