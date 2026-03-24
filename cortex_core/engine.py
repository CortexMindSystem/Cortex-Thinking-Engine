"""
CortexOS Engine
----------------
Top-level orchestrator that ties knowledge, digest processing,
post generation, scoring, context memory (4 layers), focus
recommendations, decision engine, signal detection, insights,
retrieval, and pipeline execution together.

Primary feature: "What should I focus on today?"
The real answer: "Here's what matters, why, and your next step."
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cortex_core.config import CortexConfig
from cortex_core.decisions import DecisionEngine
from cortex_core.digest import DigestProcessor
from cortex_core.focus import FocusEngine
from cortex_core.insights import InsightStore, generate_insight_from_note
from cortex_core.items import ItemStore, extract_items_from_digest, extract_items_from_summary
from cortex_core.knowledge import KnowledgeNote, KnowledgeStore
from cortex_core.llm import LLMProvider
from cortex_core.memory import ContextMemory
from cortex_core.pipeline import Pipeline
from cortex_core.posts import PostGenerator
from cortex_core.retrieve import HybridRetriever
from cortex_core.scoring import evaluate_digest
from cortex_core.signals import SignalStore, detect_signals
from cortex_core.why_engine import EvaluationContext, SourceItem, WhyEngine


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

        # New subsystems
        self.items = ItemStore(self.config.data_dir / "items.json")
        self.insights = InsightStore(self.config.data_dir / "insights.json")
        self.signal_store = SignalStore(self.config.data_dir / "signals.json")
        self.decision_engine = DecisionEngine(self.config.data_dir)
        self.retriever = HybridRetriever()
        self.why_engine = WhyEngine()

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

        pipe.add_step("Ingest items", lambda: self.ingest_digest())
        pipe.add_step("Process digest", lambda: self.process_digest(use_llm=use_llm))
        pipe.add_step("Evaluate digest", lambda: self.evaluate_digest())
        pipe.add_step("Detect signals", lambda: self.detect_signals())
        pipe.add_step("Generate insights", lambda: self.generate_insights())
        pipe.add_step("Generate focus brief", lambda: self.generate_focus_brief(use_llm=use_llm))
        pipe.add_step("Generate decision brief", lambda: self.generate_decision_brief())
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
            "version": "0.2.0",
            "data_dir": str(self.config.data_dir),
            "notes_count": self.store.count,
            "items_count": self.items.count,
            "insights_count": self.insights.count,
            "signals_count": self.signal_store.count,
            "decisions_count": len(self.decision_engine.all_decisions),
            "llm_provider": self.config.llm.provider,
            "llm_model": self.config.llm.model,
            "profile_loaded": self.memory.profile.name != "",
            "memory_layers": {
                "identity": True,
                "projects": len(self.memory.projects),
                "research_themes": len(self.memory.research.recurring_themes),
                "working_priorities": len(self.memory.working.todays_priorities),
            },
        }

    # -------------------------------------------------------- focus / daily brief

    def generate_focus_brief(
        self,
        digest_path: str | None = None,
        *,
        use_llm: bool = False,
    ) -> dict:
        """Generate today's focus recommendations.

        Passes pre-computed scored articles, insights, and signals into
        the FocusEngine so the brief reflects the full intelligence chain
        instead of re-deriving everything from scratch.
        """
        # Gather pre-computed enrichment data
        scored = self._latest_scored_articles() or []
        insights_data = [i.to_dict() for i in self.insights.recent(20)]
        signals_data = [s.to_dict() for s in self.signal_store.active_signals()]

        kwargs = dict(
            use_llm=use_llm,
            scored_articles=scored if scored else None,
            insights=insights_data if insights_data else None,
            signals=signals_data if signals_data else None,
        )

        if digest_path:
            brief = self.focus.generate_from_file(Path(digest_path), **kwargs)
        else:
            brief = self.focus.generate_from_latest(self.config.data_dir, **kwargs)
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
            "role": p.role,
            "preferred_style": p.preferred_style,
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
        score = evaluate_digest(
            content,
            ctx,
            seen_titles={e.title.lower().strip() for e in self.memory.history},
            ignored_topics=self.memory.profile.ignored_set(),
            goal_tokens=self.memory.profile.goal_tokens(),
        )
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

    # ============================================================
    # NEW: Item ingestion
    # ============================================================

    def ingest_digest(self, path: str | None = None) -> list[dict]:
        """Ingest a digest file into structured Items (raw data preservation)."""
        if path:
            text = Path(path).read_text(encoding="utf-8")
        else:
            files = sorted(self.config.data_dir.glob(self.config.digest_glob))
            if not files:
                paths = sorted(Path(".").glob("weekly_digest_*.md"))
                if not paths:
                    return []
                text = paths[-1].read_text(encoding="utf-8")
            else:
                text = files[-1].read_text(encoding="utf-8")

        raw_items = extract_items_from_digest(text)
        added = self.items.add_batch(raw_items)
        return [i.to_dict() for i in added]

    # ============================================================
    # Summary ingestion (user-authored content)
    # ============================================================

    def ingest_summary(
        self,
        text: str,
        *,
        source: str = "",
        tags: list[str] | None = None,
        create_notes: bool = True,
    ) -> dict:
        """Ingest a user-written markdown summary.

        1. Parses into Items (raw preservation)
        2. Optionally creates KnowledgeNotes for each section
        3. Returns count of items and notes created

        This is how personal analysis and summaries become
        part of the CortexOS context layer.
        """
        raw_items = extract_items_from_summary(text, source=source, tags=tags)
        added_items = self.items.add_batch(raw_items)

        notes_created: list[dict] = []
        if create_notes:
            for item in added_items:
                note = KnowledgeNote(
                    title=item.title,
                    insight=item.content,
                    implication="",
                    action="",
                    source_url=item.url,
                    tags=item.tags,
                )
                saved = self.store.add(note)
                notes_created.append(saved.to_dict())

        return {
            "items_ingested": len(added_items),
            "notes_created": len(notes_created),
            "items": [i.to_dict() for i in added_items],
            "notes": notes_created,
        }

    # ============================================================
    # NEW: Signal detection
    # ============================================================

    def detect_signals(self) -> list[dict]:
        """Detect emerging signals from all ingested items."""
        all_items = self.items.recent(200)
        titles = [i.title for i in all_items]
        urls = [i.url for i in all_items]
        new_signals = detect_signals(titles, urls=urls, min_frequency=2)
        updated = self.signal_store.update_signals(new_signals)

        # Feed confirmed signals into research memory
        for sig in self.signal_store.confirmed_signals():
            self.memory.add_research_theme(sig.topic)

        return [s.to_dict() for s in updated]

    def get_signals(self) -> list[dict]:
        """Return current active signals."""
        return [s.to_dict() for s in self.signal_store.active_signals()]

    # ============================================================
    # NEW: Insight generation
    # ============================================================

    def generate_insights(self) -> list[dict]:
        """Generate structured Insights from recent knowledge notes."""
        recent_notes = self.store.notes[-20:]
        new_insights = []
        existing_titles = {i.title for i in self.insights.insights}

        for note in recent_notes:
            if note.title in existing_titles:
                continue
            insight = generate_insight_from_note(
                title=note.title,
                insight_text=note.insight,
                implication=note.implication,
                action=note.action,
                tags=note.tags,
                source_item_id=note.id,
                project=self.memory.profile.current_projects[0] if self.memory.profile.current_projects else "",
            )
            new_insights.append(insight)

        if new_insights:
            self.insights.add_batch(new_insights)

        return [i.to_dict() for i in new_insights]

    def get_insights(self, *, limit: int = 20) -> list[dict]:
        """Return recent insights."""
        return [i.to_dict() for i in self.insights.recent(limit)]

    # ============================================================
    # NEW: Decision engine
    # ============================================================

    def generate_decision_brief(self) -> dict:
        """Generate today's decision brief from all available context."""
        # Gather scored items
        scored = [a.to_dict() for a in self._latest_scored_articles()]

        # Gather insights
        insights_data = [i.to_dict() for i in self.insights.recent(10)]

        # Gather signals
        signals_data = [s.to_dict() for s in self.signal_store.active_signals()]

        # Previous brief for change detection
        prev = self.decision_engine.get_previous_brief()

        brief = self.decision_engine.generate_brief(
            scored_items=scored,
            insights=insights_data,
            signals=signals_data,
            profile=self.memory.profile.to_dict(),
            previous_brief=prev,
        )

        # Update working memory with today's priorities
        self.memory.set_today_priorities([p.title for p in brief.priorities])

        self.decision_engine.save_brief(brief)
        return brief.to_dict()

    def record_decision(
        self,
        decision: str,
        reason: str,
        *,
        project: str = "",
        assumptions: list[str] | None = None,
    ) -> dict:
        """Record a decision with context."""
        dec = self.decision_engine.record_decision(
            decision=decision,
            reason=reason,
            project=project,
            assumptions=assumptions,
        )
        # Also add to project memory if project specified
        if project:
            self.memory.add_project_decision(project, decision)
        return dec.to_dict()

    def record_outcome(self, decision_id: str, outcome: str, impact_score: float = 0.0) -> dict | None:
        """Record the outcome of a past decision (feedback loop)."""
        dec = self.decision_engine.record_outcome(decision_id, outcome, impact_score)
        return dec.to_dict() if dec else None

    def record_feedback(self, *, item: str, useful: bool) -> None:
        """Record user feedback on a focus item (was this useful?).

        Stores in working memory so the next priority brief can
        incorporate what the user found valuable or not.
        """
        tag = "useful" if useful else "not_useful"
        self.memory.working.temporary_notes.append(f"[{tag}] {item}")

    def get_decisions(self, *, project: str | None = None, limit: int = 10) -> list[dict]:
        """Get recent decisions, optionally filtered by project."""
        if project:
            decisions = self.decision_engine.decisions_by_project(project)
        else:
            decisions = self.decision_engine.recent_decisions(limit)
        return [d.to_dict() for d in decisions]

    # ============================================================
    # NEW: Hybrid retrieval
    # ============================================================

    def retrieve(
        self,
        query: str,
        *,
        source_type: str | None = None,
        tags: list[str] | None = None,
        max_results: int = 10,
    ) -> list[dict]:
        """Search across knowledge, insights, and items."""
        # Build a unified item pool
        pool: list[dict] = []

        for note in self.store.notes:
            d = note.to_dict()
            d["source_type"] = "note"
            pool.append(d)

        for insight in self.insights.insights:
            d = insight.to_dict()
            d["source_type"] = "insight"
            d["content"] = insight.summary
            pool.append(d)

        for item in self.items.recent(100):
            pool.append(item.to_dict())

        results = self.retriever.retrieve(
            query, pool, max_results=max_results, source_type=source_type, tags=tags
        )
        return [r.to_dict() for r in results]

    # ============================================================
    # NEW: Agent Context API
    # ============================================================

    def get_active_goals(self) -> list[str]:
        return self.memory.profile.goals

    def get_project_context(self, project_name: str) -> dict:
        """Return full project context for agents."""
        pm = self.memory.get_project(project_name)
        notes = self.store.search(project_name)
        decisions = self.decision_engine.decisions_by_project(project_name)
        return {
            "project": pm.to_dict(),
            "notes_count": len(notes),
            "recent_decisions": [d.to_dict() for d in decisions[:5]],
        }

    def get_recent_decisions(self, limit: int = 5) -> list[dict]:
        return [d.to_dict() for d in self.decision_engine.recent_decisions(limit)]

    def get_priority_brief(self) -> dict | None:
        """Return today's decision brief for agents."""
        return self.decision_engine.get_previous_brief()

    def store_new_insight(self, **fields) -> dict:
        """Allow agents to store new insights."""
        from cortex_core.insights import Insight
        insight = Insight(**{k: v for k, v in fields.items() if k in Insight.__dataclass_fields__})
        self.insights.add(insight)
        return insight.to_dict()

    def get_full_context(self) -> dict:
        """Return complete memory state for agent consumption."""
        return self.memory.full_context()

    # ── Sync ────────────────────────────────────────────────────

    def build_sync_snapshot(self) -> dict:
        """Single-call snapshot of everything Apple clients need.

        Bundles profile, active project, priorities, decisions,
        insights, signals, and working memory into one dict.
        Backend is source of truth — clients pull this on launch.
        """
        from datetime import UTC, datetime

        profile = self.memory.profile

        # Active project context (first project, if any)
        active_project: dict | None = None
        if profile.current_projects:
            pm = self.memory.get_project(profile.current_projects[0])
            active_project = pm.to_dict()

        # Priority brief (may not exist yet)
        priorities = self.decision_engine.get_previous_brief()

        return {
            "profile": {
                "name": profile.name,
                "role": profile.role,
                "goals": profile.goals,
                "interests": profile.interests,
                "current_projects": profile.current_projects,
                "ignored_topics": profile.ignored_topics,
            },
            "active_project": active_project,
            "priorities": priorities,
            "recent_decisions": self.get_recent_decisions(10),
            "insights": self.get_insights(limit=10),
            "signals": self.get_signals(),
            "working_memory": self.memory.working.to_dict(),
            "synced_at": datetime.now(UTC).isoformat(),
        }

    # ── Why Engine ──────────────────────────────────────────────

    def evaluate_why(self, item_data: dict) -> dict:
        """Evaluate a single source item through the Why Engine.

        Assembles full evaluation context from all memory layers and
        returns a structured DecisionResult.
        """
        item = SourceItem.from_dict(item_data)
        context = self._build_evaluation_context()
        result = self.why_engine.evaluate(item, context)
        return result.to_dict()

    def _build_evaluation_context(self) -> EvaluationContext:
        """Assemble evaluation context from all four memory layers."""
        profile = self.memory.profile

        # Project layer: milestones, blockers from first active project
        milestones: list[str] = []
        blockers: list[str] = []
        if profile.current_projects:
            pm = self.memory.get_project(profile.current_projects[0])
            milestones = [pm.current_milestone] if pm.current_milestone else []
            blockers = list(pm.active_blockers)

        # Decision history: recent decision descriptions
        recent_decisions = [
            d.decision for d in self.decision_engine.recent_decisions(10)
        ]

        # Research layer: themes
        recent_themes = list(self.memory.research.recurring_themes)

        # Assumptions: from recent decisions
        assumptions: list[str] = []
        for d in self.decision_engine.recent_decisions(5):
            assumptions.extend(d.assumptions)

        return EvaluationContext(
            goals=profile.goals,
            interests=profile.interests,
            current_projects=profile.current_projects,
            ignored_topics=profile.ignored_topics,
            project_milestones=milestones,
            project_blockers=blockers,
            recent_decisions=recent_decisions,
            recent_themes=recent_themes,
            assumptions=assumptions,
        )

    # ── Internal helpers ────────────────────────────────────────

    def _latest_scored_articles(self) -> list:
        """Get scored articles from the latest digest."""
        from cortex_core.scoring import evaluate_digest as _eval
        files = sorted(self.config.data_dir.glob(self.config.digest_glob))
        if not files:
            paths = sorted(Path(".").glob("weekly_digest_*.md"))
            if not paths:
                return []
            content = paths[-1].read_text(encoding="utf-8")
        else:
            content = files[-1].read_text(encoding="utf-8")

        ctx = self.memory.get_context_snippets()
        score = _eval(
            content,
            ctx,
            seen_titles={e.title.lower().strip() for e in self.memory.history},
            ignored_topics=self.memory.profile.ignored_set(),
            goal_tokens=self.memory.profile.goal_tokens(),
        )
        return score.articles
