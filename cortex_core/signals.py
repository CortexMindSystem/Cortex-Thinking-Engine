"""
Signal Detection
-----------------
Detects emerging patterns across ingested items. When a topic
appears in multiple independent sources within a time window,
it becomes an "emerging signal" that feeds the Decision Engine.

This is how CortexOS identifies trends before they become obvious.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass
class Signal:
    """An emerging signal detected across multiple sources."""

    id: str = ""
    topic: str = ""
    frequency: int = 0
    first_seen: str = ""
    last_seen: str = ""
    source_titles: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
    strength: float = 0.0  # 0.0—1.0 based on frequency + recency
    status: str = "emerging"  # emerging, confirmed, fading, archived

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Signal:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Topic extraction ─────────────────────────────────────────

# Meaningful compound and single-word topics to detect
TOPIC_PATTERNS: dict[str, list[str]] = {
    "context engineering": ["context engineering", "context-engineering"],
    "agent memory": ["agent memory", "agent state", "long-running agent"],
    "ai agents": ["ai agent", "ai agents", "agentic"],
    "context windows": ["context window", "long context", "million token"],
    "retrieval augmented generation": ["rag", "retrieval augmented", "retrieval-augmented"],
    "model evaluation": ["evaluation", "benchmark", "eval framework"],
    "developer tools": ["developer tool", "dev tool", "developer productivity", "coding agent"],
    "robotics": ["robot", "robotics", "humanoid"],
    "ai safety": ["ai safety", "alignment", "ai ethics", "ai risk"],
    "open source ai": ["open source", "open-source", "llama", "mistral"],
    "multimodal ai": ["multimodal", "vision model", "image generation"],
    "knowledge graphs": ["knowledge graph", "knowledge base", "graph database"],
    "ai infrastructure": ["ai infrastructure", "gpu", "compute", "training infrastructure"],
    "decision intelligence": ["decision intelligence", "decision system", "prioritisation", "prioritization"],
    "autonomous systems": ["autonomous", "self-driving", "autopilot"],
}


def extract_topics(text: str) -> list[str]:
    """Extract recognised topics from text."""
    text_lower = text.lower()
    found: list[str] = []
    for topic, patterns in TOPIC_PATTERNS.items():
        if any(p in text_lower for p in patterns):
            found.append(topic)
    return found


def detect_signals(
    titles: list[str],
    *,
    min_frequency: int = 3,
    urls: list[str] | None = None,
) -> list[Signal]:
    """Detect emerging signals from a list of article titles.

    A signal is a topic that appears in ``min_frequency`` or more
    independent titles within the batch.
    """
    url_list = urls or [""] * len(titles)
    topic_entries: dict[str, list[tuple[str, str]]] = {}

    for title, url in zip(titles, url_list, strict=False):
        topics = extract_topics(title)
        for topic in topics:
            topic_entries.setdefault(topic, []).append((title, url))

    now = datetime.now(UTC).isoformat()
    signals: list[Signal] = []

    for topic, entries in topic_entries.items():
        if len(entries) >= min_frequency:
            titles_list = [e[0] for e in entries]
            urls_list = [e[1] for e in entries if e[1]]
            strength = min(len(entries) / 10.0, 1.0)  # cap at 1.0

            signals.append(
                Signal(
                    id=f"sig-{topic.replace(' ', '-')}",
                    topic=topic,
                    frequency=len(entries),
                    first_seen=now,
                    last_seen=now,
                    source_titles=titles_list,
                    source_urls=urls_list,
                    strength=round(strength, 2),
                    status="emerging" if len(entries) < 5 else "confirmed",
                )
            )

    return sorted(signals, key=lambda s: s.strength, reverse=True)


# ── Signal Store ─────────────────────────────────────────────


class SignalStore:
    """Persists detected signals across sessions."""

    def __init__(self, path: Path):
        self.path = path
        self._signals: list[Signal] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with open(self.path) as f:
                raw = json.load(f)
            self._signals = [Signal.from_dict(r) for r in raw]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump([s.to_dict() for s in self._signals], f, indent=2)

    def update_signals(self, new_signals: list[Signal]) -> list[Signal]:
        """Merge new signals with existing ones, updating frequencies."""
        existing_map = {s.topic: s for s in self._signals}

        for sig in new_signals:
            if sig.topic in existing_map:
                existing = existing_map[sig.topic]
                # Merge: add new sources, update frequency
                for title in sig.source_titles:
                    if title not in existing.source_titles:
                        existing.source_titles.append(title)
                for url in sig.source_urls:
                    if url and url not in existing.source_urls:
                        existing.source_urls.append(url)
                existing.frequency = len(existing.source_titles)
                existing.last_seen = sig.last_seen
                existing.strength = min(existing.frequency / 10.0, 1.0)
                if existing.frequency >= 5:
                    existing.status = "confirmed"
            else:
                existing_map[sig.topic] = sig

        self._signals = sorted(existing_map.values(), key=lambda s: s.strength, reverse=True)
        self.save()
        return self._signals

    def active_signals(self) -> list[Signal]:
        """Return non-archived signals."""
        return [s for s in self._signals if s.status != "archived"]

    def confirmed_signals(self) -> list[Signal]:
        return [s for s in self._signals if s.status == "confirmed"]

    def emerging_signals(self) -> list[Signal]:
        return [s for s in self._signals if s.status == "emerging"]

    def archive_old(self, days: int = 30) -> int:
        """Archive signals not seen in the given window."""
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        count = 0
        for s in self._signals:
            if s.last_seen < cutoff and s.status != "archived":
                s.status = "archived"
                count += 1
        if count:
            self.save()
        return count

    @property
    def count(self) -> int:
        return len(self.active_signals())

    @property
    def signals(self) -> list[Signal]:
        return list(self._signals)
