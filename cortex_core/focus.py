"""
Focus Recommendation Engine
-----------------------------
The killer feature of CortexOS. Takes scored articles, knowledge
notes, and user context to produce a ranked "What should I focus
on today?" brief. This is what separates CortexOS from every
generic AI summariser.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from cortex_core.knowledge import KnowledgeStore
from cortex_core.llm import LLMProvider
from cortex_core.memory import ContextMemory
from cortex_core.scoring import ArticleScore, evaluate_digest


@dataclass
class FocusItem:
    """A single focus recommendation."""

    rank: int
    title: str
    why_it_matters: str
    next_action: str
    source_url: str = ""
    relevance_score: float = 0.0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DailyBrief:
    """The daily focus brief — CortexOS's primary output."""

    date: str = field(default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%d"))
    focus_items: list[FocusItem] = field(default_factory=list)
    digest_quality: dict | None = None
    profile_summary: dict | None = None

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "focus_items": [i.to_dict() for i in self.focus_items],
            "digest_quality": self.digest_quality,
            "profile_summary": self.profile_summary,
        }

    def to_markdown(self) -> str:
        """Render the brief as a readable Markdown document."""
        lines = [
            f"# CortexOS Daily Focus — {self.date}",
            "",
        ]
        if not self.focus_items:
            lines.append("_No focus items today. Run the pipeline or add articles._")
        else:
            for item in self.focus_items:
                lines.extend(
                    [
                        f"## {item.rank}. {item.title}",
                        "",
                        f"**Why it matters:** {item.why_it_matters}",
                        "",
                        f"**Next action:** {item.next_action}",
                        "",
                        f"_Relevance: {item.relevance_score:.2f}_",
                    ]
                )
                if item.source_url:
                    lines.append(f"[Source]({item.source_url})")
                if item.tags:
                    lines.append(f"Tags: {', '.join(item.tags)}")
                lines.append("")

        if self.digest_quality:
            lines.extend(
                [
                    "---",
                    "### Digest Quality",
                    f"- AI article ratio: {self.digest_quality.get('ai_article_ratio', 0):.1%}",
                    f"- High signal ratio: {self.digest_quality.get('high_signal_ratio', 0):.1%}",
                    f"- Project fit score: {self.digest_quality.get('project_fit_score', 0):.1%}",
                    "",
                ]
            )

        return "\n".join(lines)


class FocusEngine:
    """Produces daily focus briefs from scored content + user context."""

    def __init__(
        self,
        memory: ContextMemory,
        store: KnowledgeStore,
        llm: LLMProvider | None = None,
    ):
        self.memory = memory
        self.store = store
        self.llm = llm

    # ── Core recommendation ─────────────────────────────────────

    def generate_brief(
        self,
        digest_text: str | None = None,
        *,
        max_items: int = 5,
        use_llm: bool = False,
    ) -> DailyBrief:
        """Generate today's focus brief."""
        context_snippets = self.memory.get_context_snippets()

        brief = DailyBrief()
        brief.profile_summary = self.memory.summary()

        # Score digest if provided
        scored_articles: list[ArticleScore] = []
        if digest_text:
            digest_score = evaluate_digest(digest_text, context_snippets)
            brief.digest_quality = {
                "total_articles": digest_score.total_articles,
                "ai_article_ratio": digest_score.ai_article_ratio,
                "high_signal_ratio": digest_score.high_signal_ratio,
                "project_fit_score": digest_score.project_fit_score,
            }
            # Filter to high-signal articles, skip already-read
            scored_articles = [
                a for a in digest_score.articles if a.composite >= 0.2 and not self.memory.already_read(a.title)
            ]

        # Also pull recent unactioned knowledge notes
        recent_notes = self.store.notes[:10]

        # Build focus items from scored articles
        focus_items: list[FocusItem] = []

        for article in scored_articles[:max_items]:
            item = self._llm_focus_item(article) if use_llm and self.llm else self._rule_focus_item(article)
            focus_items.append(item)

        # Fill remaining slots from knowledge notes
        remaining_slots = max_items - len(focus_items)
        for note in recent_notes[:remaining_slots]:
            if note.action and not any(f.title == note.title for f in focus_items):
                focus_items.append(
                    FocusItem(
                        rank=0,
                        title=note.title,
                        why_it_matters=note.implication or note.insight,
                        next_action=note.action,
                        relevance_score=0.5,
                        tags=note.tags,
                    )
                )

        # Assign final ranks
        for i, item in enumerate(focus_items[:max_items], 1):
            item.rank = i

        brief.focus_items = focus_items[:max_items]
        return brief

    # ── Focus item strategies ───────────────────────────────────

    @staticmethod
    def _rule_focus_item(article: ArticleScore) -> FocusItem:
        """Create a focus item using rule-based logic."""
        if article.ai_related:
            why = f"{article.title} signals a shift in AI systems that affects CortexOS architecture."
            action = "Read the article, extract the key insight, and add to research backlog."
        elif article.high_signal:
            why = f"{article.title} is relevant to developer productivity and system design."
            action = "Skim for applicable patterns and note any architecture implications."
        else:
            why = f"{article.title} may contain useful context for ongoing projects."
            action = "Quick review — bookmark if relevant, skip if not."

        return FocusItem(
            rank=0,
            title=article.title,
            why_it_matters=why,
            next_action=action,
            source_url=article.url,
            relevance_score=article.composite,
            tags=_infer_tags(article),
        )

    def _llm_focus_item(self, article: ArticleScore) -> FocusItem:
        """Create a focus item using LLM analysis."""
        profile = self.memory.profile
        prompt = (
            f"You are CortexOS, a thinking engine for ambitious builders.\n"
            f"User goals: {', '.join(profile.goals)}\n"
            f"User interests: {', '.join(profile.interests)}\n"
            f"Current projects: {', '.join(profile.current_projects)}\n\n"
            f"Article: {article.title}\n"
            f"URL: {article.url}\n"
            f"AI relevance: {'Yes' if article.ai_related else 'No'}\n"
            f"Score: {article.composite:.2f}\n\n"
            f"Provide a JSON object with:\n"
            f"- why_it_matters (1-2 sentences, specific to user's goals)\n"
            f"- next_action (concrete actionable step)\n"
            f"- tags (list of 2-3 topic tags)\n"
        )
        resp = self.llm.generate(prompt)  # type: ignore[union-attr]
        try:
            data = json.loads(resp.text)
        except Exception:
            return self._rule_focus_item(article)

        return FocusItem(
            rank=0,
            title=article.title,
            why_it_matters=data.get("why_it_matters", ""),
            next_action=data.get("next_action", ""),
            source_url=article.url,
            relevance_score=article.composite,
            tags=data.get("tags", []),
        )

    # ── History integration ─────────────────────────────────────

    def mark_read(self, title: str, url: str = "", insight: str = "") -> None:
        """Record that the user has read/processed a focus item."""
        self.memory.record_read(title=title, url=url, insight=insight)

    # ── File-based workflow ─────────────────────────────────────

    def generate_from_file(self, digest_path: Path, *, max_items: int = 5, use_llm: bool = False) -> DailyBrief:
        """Load a digest file and generate the brief."""
        text = digest_path.read_text(encoding="utf-8")
        return self.generate_brief(text, max_items=max_items, use_llm=use_llm)

    def generate_from_latest(self, directory: Path, *, max_items: int = 5, use_llm: bool = False) -> DailyBrief:
        """Find the latest digest and generate."""
        candidates = sorted(directory.glob("weekly_digest_*.md"))
        if not candidates:
            return self.generate_brief(max_items=max_items, use_llm=use_llm)
        return self.generate_from_file(candidates[-1], max_items=max_items, use_llm=use_llm)

    def save_brief(self, brief: DailyBrief, directory: Path) -> Path:
        """Save brief as both JSON and Markdown."""
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / f"focus_{brief.date}.json"
        md_path = directory / f"focus_{brief.date}.md"

        with open(json_path, "w") as f:
            json.dump(brief.to_dict(), f, indent=2)
        with open(md_path, "w") as f:
            f.write(brief.to_markdown())

        return md_path


def _infer_tags(article: ArticleScore) -> list[str]:
    """Infer topic tags from article title keywords."""
    tags = []
    title_lower = article.title.lower()
    tag_map = {
        "ai": ["ai", "artificial", "llm", "gpt", "claude", "gemini"],
        "agents": ["agent", "agents", "agentic"],
        "retrieval": ["retrieval", "rag", "context", "vector", "search"],
        "infrastructure": ["infrastructure", "chip", "supply", "helium"],
        "robotics": ["robot", "robotics"],
        "safety": ["safety", "psychosis", "ethics", "risk"],
        "developer-tools": ["developer", "docker", "github", "tool"],
        "productivity": ["productivity", "focus", "learning"],
    }
    for tag, keywords in tag_map.items():
        if any(kw in title_lower for kw in keywords):
            tags.append(tag)
    return tags or ["general"]
