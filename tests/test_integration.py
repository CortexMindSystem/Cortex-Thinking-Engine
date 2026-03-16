"""
Integration tests for the CortexOS self-improvement loop.

Tests the full pipeline: profile → context → digest → score → focus →
learn → re-evaluate → deduplication → spaced repetition.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from cortex_core.config import CortexConfig, LLMConfig
from cortex_core.engine import CortexEngine


@pytest.fixture
def engine(tmp_data_dir: Path, sample_digest_text: str) -> CortexEngine:
    """CortexEngine wired to a temporary data directory with a digest."""
    digest_path = tmp_data_dir / "weekly_digest_2026-03-15.md"
    digest_path.write_text(sample_digest_text)

    config = CortexConfig(
        data_dir=tmp_data_dir,
        llm=LLMConfig(provider="openai", model="gpt-4o"),
    )
    return CortexEngine(config=config)


# ── Profile & Context ──────────────────────────────────────────


class TestProfileAndContext:
    def test_set_profile(self, engine: CortexEngine):
        engine.update_profile(
            name="Tester",
            goals=["Build context engine"],
            interests=["AI", "retrieval"],
            current_projects=["CortexOS"],
        )
        p = engine.get_profile()
        assert p["name"] == "Tester"
        assert len(p["goals"]) == 1

    def test_context_snippets_include_profile(self, engine: CortexEngine):
        engine.update_profile(goals=["Ship CortexOS"], interests=["AI agents"])
        snippets = engine.memory.get_context_snippets()
        assert "Ship CortexOS" in snippets
        assert "AI agents" in snippets

    def test_context_tokens_include_profile(self, engine: CortexEngine):
        engine.update_profile(interests=["vector search"])
        tokens = engine.memory.get_context_tokens()
        assert "vector" in tokens
        assert "search" in tokens


# ── Full Pipeline ──────────────────────────────────────────────


class TestPipeline:
    def test_pipeline_all_steps_succeed(self, engine: CortexEngine):
        result = engine.run_pipeline()
        assert result["success"] is True
        assert len(result["steps"]) == 9
        for step in result["steps"]:
            assert step["status"] == "success"

    def test_pipeline_creates_notes(self, engine: CortexEngine):
        assert engine.store.count == 0
        engine.run_pipeline()
        assert engine.store.count > 0

    def test_pipeline_creates_focus_brief(self, engine: CortexEngine):
        engine.run_pipeline()
        brief = engine.get_latest_brief()
        assert brief is not None
        assert "focus_items" in brief

    def test_pipeline_exports_posts(self, engine: CortexEngine):
        engine.run_pipeline()
        posts_path = engine.config.posts_path
        assert posts_path.exists()
        assert len(posts_path.read_text()) > 0


# ── Deduplication ──────────────────────────────────────────────


class TestDeduplication:
    def test_no_duplicates_on_rerun(self, engine: CortexEngine):
        engine.run_pipeline()
        count_first = engine.store.count
        assert count_first > 0

        engine.run_pipeline()
        count_second = engine.store.count
        assert count_second == count_first

    def test_no_duplicates_triple_run(self, engine: CortexEngine):
        for _ in range(3):
            engine.run_pipeline()
        # Only one set of notes from the digest
        count = engine.store.count
        engine.run_pipeline()
        assert engine.store.count == count

    def test_add_same_note_twice(self, engine: CortexEngine):
        engine.add_note(title="Duplicate Test", source_url="https://example.com")
        engine.add_note(title="Duplicate Test", source_url="https://example.com")
        results = engine.search_notes("Duplicate Test")
        assert len(results) == 1


# ── Tag Inference ──────────────────────────────────────────────


class TestTagInference:
    def test_ai_articles_get_ai_tag(self, engine: CortexEngine):
        engine.run_pipeline()
        notes = engine.list_notes()
        ai_tagged = [n for n in notes if "ai" in n.get("tags", [])]
        assert len(ai_tagged) > 0

    def test_multiple_tag_categories(self, engine: CortexEngine):
        engine.run_pipeline()
        all_tags = set()
        for n in engine.list_notes():
            all_tags.update(n.get("tags", []))
        # Should have more than just section headings
        assert len(all_tags) > 2

    def test_non_ai_articles_get_relevant_tags(self, engine: CortexEngine):
        engine.run_pipeline()
        notes = engine.list_notes()
        all_tags = set()
        for n in notes:
            all_tags.update(n.get("tags", []))
        # Should have developer-tools or productivity from sample digest
        assert "developer-tools" in all_tags or "productivity" in all_tags


# ── Digest Evaluation ──────────────────────────────────────────


class TestDigestEvaluation:
    def test_evaluate_returns_metrics(self, engine: CortexEngine):
        result = engine.evaluate_digest()
        assert "error" not in result
        assert result["total_articles"] > 0
        assert result["ai_article_ratio"] > 0
        assert result["project_fit_score"] > 0

    def test_evaluate_returns_top_articles(self, engine: CortexEngine):
        result = engine.evaluate_digest()
        assert len(result.get("top_articles", [])) > 0
        top = result["top_articles"][0]
        assert "title" in top
        assert "score" in top


# ── Focus Brief ────────────────────────────────────────────────


class TestFocusBrief:
    def test_brief_contains_items(self, engine: CortexEngine):
        brief = engine.generate_focus_brief()
        assert len(brief.get("focus_items", [])) > 0

    def test_brief_items_have_next_action(self, engine: CortexEngine):
        brief = engine.generate_focus_brief()
        for item in brief["focus_items"]:
            assert item["next_action"] != ""

    def test_brief_includes_digest_quality(self, engine: CortexEngine):
        brief = engine.generate_focus_brief()
        assert brief.get("digest_quality") is not None
        assert "ai_article_ratio" in brief["digest_quality"]

    def test_brief_saved_to_disk(self, engine: CortexEngine):
        engine.generate_focus_brief()
        briefs = list(engine.config.data_dir.glob("focus_*.json"))
        assert len(briefs) >= 1


# ── Self-Improvement Loop ─────────────────────────────────────


class TestSelfImprovement:
    def test_context_grows_after_reading(self, engine: CortexEngine):
        ctx_before = engine.memory.get_context_snippets()
        tokens_before = engine.memory.get_context_tokens()

        engine.memory.record_read(
            title="Deep Retrieval Architecture",
            url="https://example.com/deep-retrieval",
            score=0.9,
            tags=["ai", "retrieval"],
            insight="Deep retrieval with context windows beats BM25 by 35%.",
        )

        ctx_after = engine.memory.get_context_snippets()
        tokens_after = engine.memory.get_context_tokens()
        assert len(ctx_after) > len(ctx_before)
        assert len(tokens_after) > len(tokens_before)

    def test_context_coverage_improves_with_reading(self, engine: CortexEngine):
        eval_before = engine.evaluate_digest()

        # Read something relevant to the digest
        engine.memory.record_read(
            title="AI Agent Framework Review",
            url="https://example.com/agent-review",
            score=0.85,
            tags=["ai", "agents"],
            insight="Agent frameworks need context retrieval to be useful.",
        )

        eval_after = engine.evaluate_digest()
        assert eval_after["context_keyword_coverage"] >= eval_before["context_keyword_coverage"]

    def test_focus_excludes_already_read(self, engine: CortexEngine):
        brief_before = engine.generate_focus_brief()
        first_title = brief_before["focus_items"][0]["title"]

        # Mark it as read
        engine.focus.mark_read(first_title)

        brief_after = engine.generate_focus_brief()
        after_titles = [i["title"] for i in brief_after["focus_items"]]
        assert first_title not in after_titles


# ── Spaced Repetition ─────────────────────────────────────────


class TestSpacedRepetition:
    def test_new_reading_has_next_review(self, engine: CortexEngine):
        entry = engine.memory.record_read(
            title="SRS Test Article",
            insight="Testing spaced repetition.",
        )
        assert entry.next_review != ""

    def test_due_for_review_empty_initially(self, engine: CortexEngine):
        engine.memory.record_read(title="Future Review")
        due = engine.due_for_review()
        # Just recorded — next_review is 1 day in the future
        assert len(due) == 0

    def test_due_for_review_surfaces_overdue(self, engine: CortexEngine):
        entry = engine.memory.record_read(
            title="Overdue Article",
            insight="Should be due for review.",
        )
        # Manually set next_review to the past
        entry.next_review = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        engine.memory.save()

        due = engine.due_for_review()
        assert any(d["title"] == "Overdue Article" for d in due)

    def test_advance_review_increments_level(self, engine: CortexEngine):
        engine.memory.record_read(title="Level Up Article")

        result = engine.advance_review("Level Up Article")
        assert result is not None
        assert result["review_level"] == 1

        result2 = engine.advance_review("Level Up Article")
        assert result2 is not None
        assert result2["review_level"] == 2

    def test_advance_review_nonexistent(self, engine: CortexEngine):
        result = engine.advance_review("Does Not Exist")
        assert result is None

    def test_review_intervals_increase(self, engine: CortexEngine):
        entry = engine.memory.record_read(title="Interval Test")
        first_review = entry.next_review

        advanced = engine.memory.advance_review("Interval Test")
        assert advanced is not None
        second_review = advanced.next_review

        # Second review should be further in the future than first
        assert second_review > first_review
