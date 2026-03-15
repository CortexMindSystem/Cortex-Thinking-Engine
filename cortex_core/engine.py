"""
CortexOS Engine
----------------
Top-level orchestrator that ties knowledge, digest processing,
post generation, scoring, context memory, focus recommendations,
and pipeline execution together.

Primary feature: "What should I focus on today?"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cortex_core.config import CortexConfig
from cortex_core.digest import DigestProcessor
from cortex_core.focus import FocusEngine
from cortex_core.knowledge import KnowledgeNote, KnowledgeStore
from cortex_core.llm import LLMProvider
from cortex_core.memory import ContextMemory
from cortex_core.pipeline import Pipeline
from cortex_core.posts import PostGenerator
from cortex_core.scoring import evaluate_digest


class CortexEngine:
    """Facade for all CortexOS operations."""

    def __init__(self, config: CortexConfig | None = None):
        self.config = config or CortexConfig.load()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        # Core components
        self.llm = LLMProvider(self.config.llm)
        self.store = KnowledgeStore(self.config.knowledge_path)
        self.digest = DigestProcessor(self.store, self.llm)
        self.posts = PostGenerator(self.store, self.llm)

        # Context & intelligence layer
        self.memory = ContextMemory(self.config.data_dir)
        self.focus = FocusEngine(self.memory, self.store, self.llm)

    # ------------------------------------------------------ knowledge CRUD

    def list_notes(self, *, include_archived: bool = False) -> list[dict]:
        notes = self.store.all_notes if include_archived else self.store.notes
        return [n.to_dict() for n in notes]

    def get_note(self, note_id: str) -> dict | None:
        note = self.store.get(note_id)
        return note.to_dict() if note else None

    def add_note(self, **fields) -> dict:
        note = KnowledgeNote(**{k: v for k, v in fields.items() if k in KnowledgeNote.__dataclass_fields__})
        return self.store.add(note).to_dict()

    def update_note(self, note_id: str, **fields) -> dict | None:
        note = self.store.update(note_id, **fields)
        return note.to_dict() if note else None

    def delete_note(self, note_id: str) -> bool:
        return self.store.delete(note_id)

    def search_notes(self, query: str) -> list[dict]:
        return [n.to_dict() for n in self.store.search(query)]

    # ------------------------------------------------------ digest workflow

    def process_digest(self, path: str | None = None, *, use_llm: bool = False) -> list[dict]:
        if path:
            notes = self.digest.process_file(Path(path), use_llm=use_llm)
        else:
            notes = self.digest.process_latest(self.config.data_dir, use_llm=use_llm)
        return [n.to_dict() for n in notes]

    # ------------------------------------------------------- post generation

    def generate_posts(
        self,
        *,
        limit: int = 3,
        platform: str = "general",
        use_llm: bool = False,
    ) -> list[dict]:
        posts = self.posts.generate(limit=limit, platform=platform, use_llm=use_llm)
        return [{"text": p.text, "platform": p.platform, "note_id": p.source_note_id} for p in posts]

    def export_posts(self, *, limit: int = 3, platform: str = "general") -> str:
        posts = self.posts.generate(limit=limit, platform=platform)
        out_path = self.config.posts_path
        self.posts.export(posts, out_path)
        return str(out_path)

    # -------------------------------------------------------- full pipeline

    def build_pipeline(self, *, use_llm: bool = False) -> Pipeline:
        """Create the standard CortexOS pipeline."""
        pipe = Pipeline("CortexOS Daily Pipeline")

        pipe.add_step("Process digest", lambda: self.process_digest(use_llm=use_llm))
        pipe.add_step("Evaluate digest", lambda: self.evaluate_digest())
        pipe.add_step("Generate focus brief", lambda: self.generate_focus_brief(use_llm=use_llm))
        pipe.add_step("Generate posts", lambda: self.generate_posts(use_llm=use_llm))
        pipe.add_step("Export posts", lambda: self.export_posts())

        return pipe

    def run_pipeline(self, *, use_llm: bool = False) -> dict:
        """Build and execute the full pipeline, returning results."""
        pipe = self.build_pipeline(use_llm=use_llm)
        result = pipe.run()
        return result.to_dict()

    # -------------------------------------------------------- status / info

    def status(self) -> dict:
        return {
            "version": "0.1.0",
            "data_dir": str(self.config.data_dir),
            "notes_count": self.store.count,
            "llm_provider": self.config.llm.provider,
            "llm_model": self.config.llm.model,
            "profile_loaded": self.memory.profile.name != "",
        }

    # -------------------------------------------------------- focus / daily brief

    def generate_focus_brief(
        self,
        digest_path: str | None = None,
        *,
        use_llm: bool = False,
    ) -> dict:
        """Generate today's focus recommendations."""
        if digest_path:
            brief = self.focus.generate_from_file(Path(digest_path), use_llm=use_llm)
        else:
            brief = self.focus.generate_from_latest(self.config.data_dir, use_llm=use_llm)
        self.focus.save_brief(brief, self.config.data_dir)
        return brief.to_dict()

    def get_latest_brief(self) -> dict | None:
        """Return the most recent saved focus brief, if any."""
        briefs = sorted(self.config.data_dir.glob("focus_*.json"), reverse=True)
        if not briefs:
            return None
        import json

        with open(briefs[0]) as f:
            return json.load(f)

    # -------------------------------------------------------- profile / memory

    def get_profile(self) -> dict:
        p = self.memory.profile
        return {
            "name": p.name,
            "goals": p.goals,
            "interests": p.interests,
            "current_projects": p.current_projects,
            "constraints": p.constraints,
            "ignored_topics": p.ignored_topics,
        }

    def update_profile(self, **fields: Any) -> dict:
        p = self.memory.profile
        for key, val in fields.items():
            if hasattr(p, key):
                setattr(p, key, val)
        self.memory.save()
        return self.get_profile()

    # -------------------------------------------------------- digest evaluation

    def evaluate_digest(
        self,
        path: str | None = None,
        context: list[str] | None = None,
    ) -> dict:
        """Score a digest file for quality and relevance."""
        if path:
            with open(path) as f:
                content = f.read()
        else:
            files = sorted(self.config.data_dir.glob(self.config.digest_glob))
            if not files:
                paths = sorted(Path(".").glob("weekly_digest_*.md"))
                if not paths:
                    return {"error": "No digest file found"}
                content = paths[-1].read_text()
            else:
                content = files[-1].read_text()

        ctx = context or self.memory.get_context_snippets()
        score = evaluate_digest(content, ctx)
        return {
            "total_articles": score.total_articles,
            "ai_article_ratio": round(score.ai_article_ratio, 3),
            "high_signal_ratio": round(score.high_signal_ratio, 3),
            "signal_to_noise_ratio": round(score.signal_to_noise_ratio, 3),
            "context_keyword_coverage": round(score.context_keyword_coverage, 3),
            "project_fit_score": round(score.project_fit_score, 3),
            "top_articles": [{"title": a.title, "score": round(a.composite, 3)} for a in score.articles[:5]],
        }

    # -------------------------------------------------------- spaced repetition

    def due_for_review(self) -> list[dict]:
        """Return reading entries due for spaced-repetition review."""
        entries = self.memory.due_for_review()
        return [e.to_dict() for e in entries]

    def advance_review(self, title: str) -> dict | None:
        """Mark an entry as reviewed and advance to the next interval."""
        entry = self.memory.advance_review(title)
        return entry.to_dict() if entry else None
