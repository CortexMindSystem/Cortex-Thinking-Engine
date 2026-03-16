"""
Context Memory — The Moat
--------------------------
CortexOS's most important subsystem. Structured memory split
into four layers:

  1. Identity memory  — stable facts about the user
  2. Project memory   — per-project state, milestones, decisions
  3. Research memory  — recurring themes, open questions
  4. Working memory   — short-lived daily priorities and state

Do not dump everything into one vector database and call it memory.
This is the correct model.

Also includes spaced-repetition scheduling for reading history.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cortex_core.scoring import tokenize

# Spaced repetition intervals in days (Leitner-style)
REVIEW_INTERVALS: list[int] = [1, 3, 7, 14, 30]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 1: Identity Memory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class UserProfile:
    """The user's identity context — stable, long-term facts."""

    name: str = "Builder"
    role: str = "AI Systems Builder"
    preferred_style: str = "concise, technical, action-oriented"
    goals: list[str] = field(
        default_factory=lambda: [
            "Build CortexOS context engine",
            "Improve AI systems design skills",
            "Publish weekly technical content",
        ]
    )
    interests: list[str] = field(
        default_factory=lambda: [
            "AI agents",
            "context memory",
            "retrieval",
            "evaluation",
            "developer productivity",
            "knowledge systems",
            "learning",
        ]
    )
    current_projects: list[str] = field(
        default_factory=lambda: [
            "CortexOS",
        ]
    )
    constraints: list[str] = field(
        default_factory=lambda: [
            "Low code debt",
            "Fast iteration",
            "AI-maintainable codebase",
        ]
    )
    ignored_topics: list[str] = field(
        default_factory=lambda: [
            "celebrity news",
            "entertainment",
            "social media drama",
        ]
    )

    def context_tokens(self) -> set[str]:
        """Flatten profile into a searchable token set."""
        text = " ".join(self.goals + self.interests + self.current_projects + self.constraints)
        return set(tokenize(text))

    def goal_tokens(self) -> set[str]:
        """Tokens derived only from goals and projects — for project_relevance scoring."""
        text = " ".join(self.goals + self.current_projects)
        return set(tokenize(text))

    def ignored_set(self) -> set[str]:
        """Return ignored topics as a lowercase set for scoring."""
        return {t.lower() for t in self.ignored_topics}

    def context_snippets(self) -> list[str]:
        """Return profile as context snippets for the scoring engine."""
        snippets = []
        snippets.extend(self.goals)
        snippets.extend(self.interests)
        snippets.extend(self.current_projects)
        return snippets

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UserProfile:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 2: Project Memory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class ProjectMemory:
    """Per-project state: milestones, blockers, decisions, architecture."""

    project_name: str = ""
    current_milestone: str = ""
    active_blockers: list[str] = field(default_factory=list)
    recent_decisions: list[str] = field(default_factory=list)
    architecture_notes: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ProjectMemory:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 3: Research Memory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class ResearchMemory:
    """Cross-session research state: recurring themes, linked topics."""

    recurring_themes: list[str] = field(default_factory=list)
    linked_topics: dict[str, list[str]] = field(default_factory=dict)  # topic → related topics
    open_questions: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def add_theme(self, theme: str) -> None:
        if theme not in self.recurring_themes:
            self.recurring_themes.append(theme)

    def add_question(self, question: str) -> None:
        if question not in self.open_questions:
            self.open_questions.append(question)

    def add_contradiction(self, note: str) -> None:
        if note not in self.contradictions:
            self.contradictions.append(note)

    def link_topics(self, topic: str, related: str) -> None:
        self.linked_topics.setdefault(topic, [])
        if related not in self.linked_topics[topic]:
            self.linked_topics[topic].append(related)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ResearchMemory:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Layer 4: Working Memory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class WorkingMemory:
    """Short-lived state: today's priorities, what's being explored."""

    date: str = field(default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%d"))
    todays_priorities: list[str] = field(default_factory=list)
    currently_exploring: list[str] = field(default_factory=list)
    temporary_notes: list[str] = field(default_factory=list)

    def set_priorities(self, priorities: list[str]) -> None:
        self.todays_priorities = priorities
        self.date = datetime.now(UTC).strftime("%Y-%m-%d")

    def add_exploration(self, topic: str) -> None:
        if topic not in self.currently_exploring:
            self.currently_exploring.append(topic)

    def add_note(self, note: str) -> None:
        self.temporary_notes.append(note)

    def clear_if_stale(self) -> bool:
        """Reset working memory if it's from a previous day."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if self.date != today:
            self.date = today
            self.todays_priorities = []
            self.currently_exploring = []
            self.temporary_notes = []
            return True
        return False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> WorkingMemory:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ReadingEntry:
    """A record of something the user read or processed."""

    title: str
    url: str = ""
    read_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    insight: str = ""
    review_level: int = 0  # 0‑based index into REVIEW_INTERVALS
    next_review: str = ""  # ISO timestamp of next review

    def __post_init__(self) -> None:
        if not self.next_review and self.read_at:
            self._schedule_next_review()

    def _schedule_next_review(self) -> None:
        """Set next_review based on current review_level."""
        try:
            base = datetime.fromisoformat(self.read_at)
        except (ValueError, TypeError):
            base = datetime.now(UTC)
        interval = REVIEW_INTERVALS[min(self.review_level, len(REVIEW_INTERVALS) - 1)]
        self.next_review = (base + timedelta(days=interval)).isoformat()

    def advance_review(self) -> None:
        """Promote to the next spaced-repetition level."""
        self.review_level = min(self.review_level + 1, len(REVIEW_INTERVALS) - 1)
        # Re-anchor from now
        self.read_at = datetime.now(UTC).isoformat()
        self._schedule_next_review()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ReadingEntry:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ContextMemory:
    """Persistent context memory — all four layers + reading history."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._profile_path = data_dir / "profile.json"
        self._history_path = data_dir / "reading_history.json"
        self._projects_path = data_dir / "project_memory.json"
        self._research_path = data_dir / "research_memory.json"
        self._working_path = data_dir / "working_memory.json"

        # Layer 1: Identity
        self.profile = UserProfile()
        self.history: list[ReadingEntry] = []

        # Layer 2: Project
        self.projects: dict[str, ProjectMemory] = {}

        # Layer 3: Research
        self.research = ResearchMemory()

        # Layer 4: Working
        self.working = WorkingMemory()

        self._load()

    # ── Persistence ─────────────────────────────────────────────

    def _load(self) -> None:
        if self._profile_path.exists():
            with open(self._profile_path) as f:
                self.profile = UserProfile.from_dict(json.load(f))
        if self._history_path.exists():
            with open(self._history_path) as f:
                self.history = [ReadingEntry.from_dict(e) for e in json.load(f)]
        if self._projects_path.exists():
            with open(self._projects_path) as f:
                raw = json.load(f)
                self.projects = {k: ProjectMemory.from_dict(v) for k, v in raw.items()}
        if self._research_path.exists():
            with open(self._research_path) as f:
                self.research = ResearchMemory.from_dict(json.load(f))
        if self._working_path.exists():
            with open(self._working_path) as f:
                self.working = WorkingMemory.from_dict(json.load(f))
            self.working.clear_if_stale()

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._profile_path, "w") as f:
            json.dump(self.profile.to_dict(), f, indent=2)
        with open(self._history_path, "w") as f:
            json.dump([e.to_dict() for e in self.history], f, indent=2)
        with open(self._projects_path, "w") as f:
            json.dump({k: v.to_dict() for k, v in self.projects.items()}, f, indent=2)
        with open(self._research_path, "w") as f:
            json.dump(self.research.to_dict(), f, indent=2)
        with open(self._working_path, "w") as f:
            json.dump(self.working.to_dict(), f, indent=2)

    # ── Profile management ──────────────────────────────────────

    def update_profile(self, **fields) -> UserProfile:
        for key, value in fields.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        self.save()
        return self.profile

    def add_goal(self, goal: str) -> None:
        if goal not in self.profile.goals:
            self.profile.goals.append(goal)
            self.save()

    def add_interest(self, interest: str) -> None:
        if interest not in self.profile.interests:
            self.profile.interests.append(interest)
            self.save()

    def add_project(self, project: str) -> None:
        if project not in self.profile.current_projects:
            self.profile.current_projects.append(project)
            self.save()

    # ── Layer 2: Project memory ─────────────────────────────────

    def get_project(self, name: str) -> ProjectMemory:
        """Get or create a project memory."""
        if name not in self.projects:
            self.projects[name] = ProjectMemory(project_name=name)
            self.save()
        return self.projects[name]

    def update_project(self, name: str, **fields) -> ProjectMemory:
        """Update project memory fields."""
        pm = self.get_project(name)
        for key, val in fields.items():
            if hasattr(pm, key):
                setattr(pm, key, val)
        self.save()
        return pm

    def add_project_decision(self, project: str, decision: str) -> None:
        pm = self.get_project(project)
        pm.recent_decisions.append(decision)
        self.save()

    def add_project_blocker(self, project: str, blocker: str) -> None:
        pm = self.get_project(project)
        if blocker not in pm.active_blockers:
            pm.active_blockers.append(blocker)
            self.save()

    def resolve_blocker(self, project: str, blocker: str) -> bool:
        pm = self.get_project(project)
        if blocker in pm.active_blockers:
            pm.active_blockers.remove(blocker)
            self.save()
            return True
        return False

    # ── Layer 3: Research memory ────────────────────────────────

    def add_research_theme(self, theme: str) -> None:
        self.research.add_theme(theme)
        self.save()

    def add_research_question(self, question: str) -> None:
        self.research.add_question(question)
        self.save()

    def add_research_contradiction(self, note: str) -> None:
        self.research.add_contradiction(note)
        self.save()

    def link_research_topics(self, topic: str, related: str) -> None:
        self.research.link_topics(topic, related)
        self.save()

    # ── Layer 4: Working memory ─────────────────────────────────

    def set_today_priorities(self, priorities: list[str]) -> None:
        self.working.set_priorities(priorities)
        self.save()

    def add_exploration(self, topic: str) -> None:
        self.working.add_exploration(topic)
        self.save()

    def add_working_note(self, note: str) -> None:
        self.working.add_note(note)
        self.save()

    # ── Reading history ─────────────────────────────────────────

    def record_read(
        self, title: str, url: str = "", score: float = 0.0, tags: list[str] | None = None, insight: str = ""
    ) -> ReadingEntry:
        entry = ReadingEntry(
            title=title,
            url=url,
            score=score,
            tags=tags or [],
            insight=insight,
        )
        self.history.append(entry)
        self.save()
        return entry

    def recent_reads(self, limit: int = 20) -> list[ReadingEntry]:
        return self.history[-limit:]

    def already_read(self, title: str) -> bool:
        return any(e.title.lower() == title.lower() for e in self.history)

    # ── Context for scoring ─────────────────────────────────────

    def get_context_snippets(self) -> list[str]:
        """Return enriched context snippets including recent reads."""
        snippets = self.profile.context_snippets()
        for entry in self.recent_reads(10):
            if entry.insight:
                snippets.append(entry.insight)
            # Also extract tag-based context for richer overlap
            for tag in entry.tags:
                if tag not in snippets:
                    snippets.append(tag)
        return snippets

    def get_context_tokens(self) -> set[str]:
        tokens = self.profile.context_tokens()
        for entry in self.recent_reads(10):
            tokens.update(tokenize(entry.title))
            tokens.update(tokenize(entry.insight))
            for tag in entry.tags:
                tokens.update(tokenize(tag))
        return tokens

    # ── Spaced repetition ───────────────────────────────────────

    def due_for_review(self, *, now: datetime | None = None) -> list[ReadingEntry]:
        """Return reading entries whose next_review date has arrived."""
        ref = now or datetime.now(UTC)
        due: list[ReadingEntry] = []
        for entry in self.history:
            if not entry.next_review:
                continue
            try:
                review_dt = datetime.fromisoformat(entry.next_review)
            except (ValueError, TypeError):
                continue
            if review_dt <= ref:
                due.append(entry)
        return due

    def advance_review(self, title: str) -> ReadingEntry | None:
        """Mark a reading entry as reviewed and advance to next interval."""
        for entry in self.history:
            if entry.title.lower() == title.lower():
                entry.advance_review()
                self.save()
                return entry
        return None

    # ── Stats ───────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "name": self.profile.name,
            "role": self.profile.role,
            "goals_count": len(self.profile.goals),
            "interests_count": len(self.profile.interests),
            "projects_count": len(self.profile.current_projects),
            "total_reads": len(self.history),
            "project_memories": len(self.projects),
            "research_themes": len(self.research.recurring_themes),
            "open_questions": len(self.research.open_questions),
            "todays_priorities": len(self.working.todays_priorities),
        }

    def full_context(self) -> dict:
        """Return complete memory state for agent consumption."""
        return {
            "identity": self.profile.to_dict(),
            "projects": {k: v.to_dict() for k, v in self.projects.items()},
            "research": self.research.to_dict(),
            "working": self.working.to_dict(),
            "recent_reads": [e.to_dict() for e in self.recent_reads(10)],
        }
