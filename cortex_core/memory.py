"""
Context Memory
---------------
Stores and manages the user's profile: goals, interests, projects,
constraints, and reading history. This is CortexOS's real moat —
the system that makes recommendations personal and evolving.

Includes spaced-repetition scheduling: notes are surfaced again
at increasing intervals (1, 3, 7, 14, 30 days) to reinforce learning.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cortex_core.scoring import tokenize

# Spaced repetition intervals in days (Leitner-style)
REVIEW_INTERVALS: list[int] = [1, 3, 7, 14, 30]


@dataclass
class UserProfile:
    """The user's current context — goals, interests, constraints."""

    name: str = "Builder"
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
    """Persistent context memory — profile + reading history."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._profile_path = data_dir / "profile.json"
        self._history_path = data_dir / "reading_history.json"
        self.profile = UserProfile()
        self.history: list[ReadingEntry] = []
        self._load()

    # ── Persistence ─────────────────────────────────────────────

    def _load(self) -> None:
        if self._profile_path.exists():
            with open(self._profile_path) as f:
                self.profile = UserProfile.from_dict(json.load(f))
        if self._history_path.exists():
            with open(self._history_path) as f:
                self.history = [ReadingEntry.from_dict(e) for e in json.load(f)]

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._profile_path, "w") as f:
            json.dump(self.profile.to_dict(), f, indent=2)
        with open(self._history_path, "w") as f:
            json.dump([e.to_dict() for e in self.history], f, indent=2)

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
            "goals_count": len(self.profile.goals),
            "interests_count": len(self.profile.interests),
            "projects_count": len(self.profile.current_projects),
            "total_reads": len(self.history),
        }
