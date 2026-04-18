"""Unit tests for the CortexOS engine (facade)."""

from pathlib import Path

from cortex_core.config import CortexConfig
from cortex_core.engine import CortexEngine


def _make_engine(tmp_data_dir: Path) -> CortexEngine:
    """Create an engine with an isolated data directory."""
    config = CortexConfig(data_dir=tmp_data_dir)
    return CortexEngine(config)


class TestEngineStatus:
    def test_status_returns_dict(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        s = engine.status()
        assert s["version"] == "0.2.0"
        assert s["notes_count"] == 0
        assert "llm_provider" in s

    def test_profile_loaded_flag(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        assert "profile_loaded" in engine.status()


class TestEngineNotes:
    def test_add_and_list(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        note = engine.add_note(title="Test Note", insight="Key insight")
        assert note["title"] == "Test Note"
        notes = engine.list_notes()
        assert len(notes) == 1

    def test_get_note(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        note = engine.add_note(title="Findme")
        fetched = engine.get_note(note["id"])
        assert fetched is not None
        assert fetched["title"] == "Findme"

    def test_get_nonexistent(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        assert engine.get_note("nope") is None

    def test_update_note(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        note = engine.add_note(title="Before")
        updated = engine.update_note(note["id"], title="After")
        assert updated["title"] == "After"

    def test_delete_note(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        note = engine.add_note(title="Delete me")
        assert engine.delete_note(note["id"]) is True
        assert engine.list_notes() == []

    def test_search_notes(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        engine.add_note(title="AI Agents", insight="Context matters")
        engine.add_note(title="Cooking 101", insight="Use butter")
        results = engine.search_notes("agents")
        assert len(results) == 1


class TestEngineProfile:
    def test_get_profile(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        p = engine.get_profile()
        assert "name" in p
        assert "goals" in p
        assert "interests" in p

    def test_update_profile(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        p = engine.update_profile(name="Pierre", goals=["Ship CortexOS"])
        assert p["name"] == "Pierre"
        assert p["goals"] == ["Ship CortexOS"]

        # Verify persisted
        engine2 = _make_engine(tmp_data_dir)
        assert engine2.get_profile()["name"] == "Pierre"


class TestEngineFocus:
    def test_generate_focus_brief_empty(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        brief = engine.generate_focus_brief()
        assert "date" in brief
        assert "focus_items" in brief

    def test_generate_focus_brief_with_digest(self, tmp_data_dir, sample_digest_text):
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        engine = _make_engine(tmp_data_dir)
        brief = engine.generate_focus_brief(str(digest_path))
        assert len(brief["focus_items"]) > 0

    def test_get_latest_brief_none(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        assert engine.get_latest_brief() is None

    def test_get_latest_brief_after_generate(self, tmp_data_dir, sample_digest_text):
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        engine = _make_engine(tmp_data_dir)
        engine.generate_focus_brief(str(digest_path))
        latest = engine.get_latest_brief()
        assert latest is not None
        assert "focus_items" in latest


class TestEngineDigestEvaluation:
    def test_evaluate_digest_with_file(self, tmp_data_dir, sample_digest_text):
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        engine = _make_engine(tmp_data_dir)
        result = engine.evaluate_digest(path=str(digest_path))
        assert "total_articles" in result
        assert result["total_articles"] > 0
        assert "ai_article_ratio" in result

    def test_evaluate_digest_no_file(self, tmp_data_dir, monkeypatch):
        monkeypatch.chdir(tmp_data_dir)
        engine = _make_engine(tmp_data_dir)
        result = engine.evaluate_digest()
        assert "error" in result


class TestEnginePipeline:
    def test_run_pipeline(self, tmp_data_dir, sample_digest_text):
        # Provide a digest so the pipeline has something to process
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        engine = _make_engine(tmp_data_dir)
        result = engine.run_pipeline()
        assert "success" in result
        assert "steps" in result


class TestEngineWeeklyReview:
    def test_build_weekly_review_output_returns_none_without_artifacts(self, tmp_data_dir):
        engine = _make_engine(tmp_data_dir)
        assert engine.build_weekly_review_output() is None

    def test_build_weekly_review_output_aggregates_recent_artifacts(self, tmp_data_dir):
        import json

        payloads = {
            "2026-04-12": {
                "date": "2026-04-12",
                "priorities": [{"title": "Build sync layer"}, {"title": "Improve offline queue"}],
                "ignored": ["low signal one"],
                "emerging_signals": ["Edge AI"],
                "changes_since_yesterday": [],
            },
            "2026-04-13": {
                "date": "2026-04-13",
                "priorities": [{"title": "Build sync layer"}, {"title": "Ship TestFlight"}],
                "ignored": ["low signal two", "low signal three"],
                "emerging_signals": ["Edge AI", "On-device models"],
                "changes_since_yesterday": [],
            },
            "2026-04-18": {
                "date": "2026-04-18",
                "priorities": [{"title": "Ship TestFlight"}, {"title": "Weekly review loop"}],
                "ignored": ["low signal four"],
                "emerging_signals": ["On-device models"],
                "changes_since_yesterday": [],
            },
            "2026-04-01": {
                "date": "2026-04-01",
                "priorities": [{"title": "Out of range"}],
                "ignored": ["too old"],
                "emerging_signals": ["Old signal"],
                "changes_since_yesterday": [],
            },
        }

        for day, payload in payloads.items():
            (tmp_data_dir / f"decision_{day}.json").write_text(json.dumps(payload), encoding="utf-8")

        engine = _make_engine(tmp_data_dir)
        review = engine.build_weekly_review_output()

        assert review is not None
        assert review["week_start"] == "2026-04-12"
        assert review["week_end"] == "2026-04-18"
        assert review["days_covered"] == 3
        assert review["quality"] == "insufficient_history"
        assert review["confidence"] == 0.43
        assert review["total_ignored_signals"] == 4

        priorities = {item["title"]: item["count"] for item in review["top_priorities"]}
        assert priorities["Build sync layer"] == 2
        assert priorities["Ship TestFlight"] == 2
        assert "Out of range" not in priorities

        signals = {item["title"]: item["count"] for item in review["top_signals"]}
        assert signals["Edge AI"] == 2
        assert signals["On-device models"] == 2
        assert "Old signal" not in signals
