"""
Knowledge Note Manager
-----------------------
CRUD operations over the JSON-backed knowledge store.
Each note captures a title, insight, implication, action item,
optional tags, and timestamps.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class KnowledgeNote:
    """A single knowledge note."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    insight: str = ""
    implication: str = ""
    action: str = ""
    source_url: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = ""
    archived: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeNote:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class KnowledgeStore:
    """Manages a collection of KnowledgeNotes backed by a JSON file."""

    def __init__(self, path: Path):
        self.path = path
        self._notes: list[KnowledgeNote] = []
        self._load()

    # -------------------------------------------------------------------- io

    def _load(self) -> None:
        if self.path.exists():
            with open(self.path) as f:
                raw = json.load(f)
            self._notes = [KnowledgeNote.from_dict(r) for r in raw]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump([n.to_dict() for n in self._notes], f, indent=2)

    # ------------------------------------------------------------------ CRUD

    @property
    def notes(self) -> list[KnowledgeNote]:
        return [n for n in self._notes if not n.archived]

    @property
    def all_notes(self) -> list[KnowledgeNote]:
        return list(self._notes)

    def get(self, note_id: str) -> KnowledgeNote | None:
        for n in self._notes:
            if n.id == note_id:
                return n
        return None

    def add(self, note: KnowledgeNote, *, deduplicate: bool = True) -> KnowledgeNote:
        """Add a note. Skip if a note with the same title+URL already exists."""
        if deduplicate and self._is_duplicate(note):
            existing = self._find_by_title_url(note.title, note.source_url)
            return existing  # type: ignore[return-value]
        note.created_at = datetime.now(UTC).isoformat()
        self._notes.append(note)
        self.save()
        return note

    def _is_duplicate(self, note: KnowledgeNote) -> bool:
        """Check if a note with the same title and URL already exists."""
        return self._find_by_title_url(note.title, note.source_url) is not None

    def _find_by_title_url(self, title: str, url: str) -> KnowledgeNote | None:
        """Find an existing note by title and source URL."""
        title_lower = title.lower().strip()
        for n in self._notes:
            if n.title.lower().strip() == title_lower and (not url or not n.source_url or n.source_url == url):
                return n
        return None

    def update(self, note_id: str, **fields) -> KnowledgeNote | None:
        note = self.get(note_id)
        if note is None:
            return None
        for key, value in fields.items():
            if hasattr(note, key):
                setattr(note, key, value)
        note.updated_at = datetime.now(UTC).isoformat()
        self.save()
        return note

    def delete(self, note_id: str) -> bool:
        note = self.get(note_id)
        if note is None:
            return False
        self._notes = [n for n in self._notes if n.id != note_id]
        self.save()
        return True

    def archive(self, note_id: str) -> bool:
        return self.update(note_id, archived=True) is not None

    # --------------------------------------------------------------- search

    def search(self, query: str, *, include_archived: bool = False) -> list[KnowledgeNote]:
        query_lower = query.lower()
        results = []
        source = self._notes if include_archived else self.notes
        for note in source:
            haystack = f"{note.title} {note.insight} {note.implication} {note.action} {' '.join(note.tags)}"
            if query_lower in haystack.lower():
                results.append(note)
        return results

    def by_tag(self, tag: str) -> list[KnowledgeNote]:
        tag_lower = tag.lower()
        return [n for n in self.notes if tag_lower in [t.lower() for t in n.tags]]

    # --------------------------------------------------------------- stats

    @property
    def count(self) -> int:
        return len(self.notes)

    def summary(self) -> dict:
        all_tags: dict[str, int] = {}
        for n in self.notes:
            for t in n.tags:
                all_tags[t] = all_tags.get(t, 0) + 1
        return {
            "total": self.count,
            "archived": len([n for n in self._notes if n.archived]),
            "tags": all_tags,
        }
