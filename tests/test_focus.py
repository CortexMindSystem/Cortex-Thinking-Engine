"""Unit tests for the focus recommendation engine."""

from cortex_core.focus import DailyBrief, FocusEngine, FocusItem, _infer_tags
from cortex_core.knowledge import KnowledgeNote, KnowledgeStore
from cortex_core.memory import ContextMemory
from cortex_core.scoring import ArticleScore


class TestFocusItem:
    def test_to_dict(self):
        item = FocusItem(
            rank=1,
            title="AI Agents",
            why_it_matters="Relevant to CortexOS",
            next_action="Read and extract insights",
            relevance_score=0.8,
            tags=["ai"],
        )
        d = item.to_dict()
        assert d["rank"] == 1
        assert d["title"] == "AI Agents"
        assert d["tags"] == ["ai"]


class TestDailyBrief:
    def test_empty_brief(self):
        brief = DailyBrief()
        assert len(brief.focus_items) == 0
        assert brief.date  # auto-filled

    def test_to_dict(self):
        brief = DailyBrief(focus_items=[FocusItem(rank=1, title="T", why_it_matters="W", next_action="N")])
        d = brief.to_dict()
        assert len(d["focus_items"]) == 1
        assert d["focus_items"][0]["title"] == "T"

    def test_to_markdown_empty(self):
        brief = DailyBrief()
        md = brief.to_markdown()
        assert "No focus items today" in md

    def test_to_markdown_with_items(self):
        brief = DailyBrief(
            focus_items=[
                FocusItem(
                    rank=1,
                    title="AI Agents",
                    why_it_matters="Core to CortexOS",
                    next_action="Read the paper",
                    relevance_score=0.9,
                    tags=["ai"],
                )
            ]
        )
        md = brief.to_markdown()
        assert "AI Agents" in md
        assert "Core to CortexOS" in md
        assert "Read the paper" in md

    def test_to_markdown_with_digest_quality(self):
        brief = DailyBrief(
            digest_quality={
                "ai_article_ratio": 0.75,
                "high_signal_ratio": 0.5,
                "project_fit_score": 0.6,
            }
        )
        md = brief.to_markdown()
        assert "Digest Quality" in md


class TestInferTags:
    def test_ai_tags(self):
        article = ArticleScore(title="New LLM benchmark released", composite=0.5)
        tags = _infer_tags(article)
        assert "ai" in tags

    def test_robotics_tags(self):
        article = ArticleScore(title="Robotics startup launches", composite=0.3)
        tags = _infer_tags(article)
        assert "robotics" in tags

    def test_default_general(self):
        article = ArticleScore(title="Quarterly earnings report", composite=0.1)
        tags = _infer_tags(article)
        assert "general" in tags


class TestFocusEngine:
    def _make_engine(self, tmp_data_dir):
        mem = ContextMemory(tmp_data_dir)
        store = KnowledgeStore(tmp_data_dir / "notes.json")
        return FocusEngine(mem, store)

    def test_generate_empty_brief(self, tmp_data_dir):
        engine = self._make_engine(tmp_data_dir)
        brief = engine.generate_brief()
        assert isinstance(brief, DailyBrief)

    def test_generate_with_digest(self, tmp_data_dir, sample_digest_text):
        engine = self._make_engine(tmp_data_dir)
        brief = engine.generate_brief(sample_digest_text, max_items=3)
        assert len(brief.focus_items) <= 3
        assert brief.digest_quality is not None
        assert brief.digest_quality["total_articles"] > 0

    def test_focus_items_have_ranks(self, tmp_data_dir, sample_digest_text):
        engine = self._make_engine(tmp_data_dir)
        brief = engine.generate_brief(sample_digest_text, max_items=5)
        for i, item in enumerate(brief.focus_items, 1):
            assert item.rank == i

    def test_focus_items_have_actions(self, tmp_data_dir, sample_digest_text):
        engine = self._make_engine(tmp_data_dir)
        brief = engine.generate_brief(sample_digest_text)
        for item in brief.focus_items:
            assert item.why_it_matters
            assert item.next_action

    def test_skips_already_read(self, tmp_data_dir, sample_digest_text):
        engine = self._make_engine(tmp_data_dir)
        # Mark one article as read
        engine.memory.record_read("OpenAI launches new AI agent framework")
        brief = engine.generate_brief(sample_digest_text)
        titles = [item.title for item in brief.focus_items]
        assert "OpenAI launches new AI agent framework" not in titles

    def test_fills_from_notes(self, tmp_data_dir):
        engine = self._make_engine(tmp_data_dir)
        engine.store.add(
            KnowledgeNote(
                title="Important Note",
                implication="Relevant insight",
                action="Review the design",
                tags=["ai"],
            )
        )
        brief = engine.generate_brief(max_items=5)
        titles = [item.title for item in brief.focus_items]
        assert "Important Note" in titles

    def test_generate_from_file(self, tmp_data_dir, sample_digest_text):
        digest_path = tmp_data_dir / "weekly_digest_2026-03-14.md"
        digest_path.write_text(sample_digest_text)
        engine = self._make_engine(tmp_data_dir)
        brief = engine.generate_from_file(digest_path)
        assert len(brief.focus_items) > 0

    def test_save_brief(self, tmp_data_dir):
        engine = self._make_engine(tmp_data_dir)
        brief = DailyBrief(date="2026-03-14")
        path = engine.save_brief(brief, tmp_data_dir)
        assert path.exists()
        assert (tmp_data_dir / "focus_2026-03-14.json").exists()

    def test_mark_read(self, tmp_data_dir):
        engine = self._make_engine(tmp_data_dir)
        engine.mark_read("Some Article", url="https://example.com", insight="Key point")
        assert engine.memory.already_read("Some Article")
