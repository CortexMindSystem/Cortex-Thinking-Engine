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
