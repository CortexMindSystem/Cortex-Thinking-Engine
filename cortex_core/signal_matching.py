"""Deterministic signal matching core for SimpliXio.

This module treats every captured input as a signal and produces
inspectable ranked outputs for:
- what matters now
- decision queue
- action-ready queue
- recurring patterns
- unresolved tensions
- content candidates

V1 goals: simple, explicit, deterministic, debuggable.
"""

from __future__ import annotations

import json
import math
import re
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VALID_TYPES = {
    "thought",
    "decision",
    "task",
    "question",
    "tension",
    "reflection",
    "idea",
    "content_seed",
}

VALID_SENSITIVITY = {
    "private",
    "sensitive",
    "internal",
    "public_safe",
    "public_ready",
}

SENSITIVITY_RANK = {
    "private": 0,
    "sensitive": 1,
    "internal": 2,
    "public_safe": 3,
    "public_ready": 4,
}

SOURCE_WEIGHTS = {
    "decision": 1.00,
    "tension": 0.90,
    "recurring_frustration": 0.85,
    "task": 0.82,
    "question": 0.70,
    "thought": 0.65,
    "idea": 0.60,
    "reflection": 0.55,
    "content_seed": 0.60,
}

TYPE_HINT_MAP = {
    "note": "thought",
    "capture": "thought",
    "quick_capture": "thought",
    "decision": "decision",
    "feedback": "reflection",
}

PRIVATE_TERMS = {
    "private",
    "do not publish",
    "do-not-publish",
    "personal",
    "family",
}

INTERNAL_TERMS = {
    "internal",
    "client",
    "work",
    "workplace",
    "nda",
    "confidential",
}

SENSITIVE_TERMS = {
    "health",
    "visa",
    "immigration",
    "salary",
    "revenue",
    "bank",
    "token",
    "password",
    "secret",
    "api key",
    "credential",
}

QUESTION_TERMS = {"why", "how", "what", "when", "which", "should", "can", "could"}
TENSION_TERMS = {"stuck", "blocked", "frustrated", "conflict", "overwhelmed", "tension", "unclear"}
DECISION_TERMS = {"decide", "decision", "choose", "tradeoff", "option", "commit"}
TASK_TERMS = {"todo", "ship", "fix", "write", "send", "review", "build", "implement"}
IDEA_TERMS = {"idea", "concept", "experiment", "hypothesis", "insight"}
REFLECTION_TERMS = {"learned", "noticed", "realized", "reflection", "lesson"}

ACTION_VERBS = {
    "ship",
    "write",
    "call",
    "send",
    "fix",
    "review",
    "merge",
    "implement",
    "draft",
    "publish",
    "test",
    "decide",
}

AMBIGUOUS_TERMS = {"maybe", "someday", "perhaps", "might", "not sure", "unclear", "later"}

TONE_KEYWORDS = {
    "stressed": {"stressed", "overwhelmed", "anxious", "urgent", "pressure", "panic"},
    "excited": {"excited", "energized", "pumped", "great", "win", "momentum"},
    "uncertain": {"unsure", "uncertain", "doubt", "confused", "unclear"},
}

TIME_HORIZONS = ("now", "today", "this_week", "later")

# Calm defaults for surfaced queues (backend-enforced).
QUEUE_LIMITS = {
    "top_priorities": 3,
    "what_matters_now": 3,
    "decision_queue": 5,
    "action_ready_queue": 5,
    "recurring_patterns": 5,
    "unresolved_tensions": 5,
    "content_candidates": 5,
}


@dataclass
class SignalEvent:
    id: str
    captured_at: str
    source: str
    source_id: str
    raw_text: str
    context: str = ""
    project: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SignalScores:
    importance: float = 0.0
    clarity: float = 0.0
    decision_readiness: float = 0.0
    action_readiness: float = 0.0
    recurrence: float = 0.0
    emotional_intensity: float = 0.0
    publishability: float = 0.0
    staleness: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "importance": round(self.importance, 2),
            "clarity": round(self.clarity, 2),
            "decision_readiness": round(self.decision_readiness, 2),
            "action_readiness": round(self.action_readiness, 2),
            "recurrence": round(self.recurrence, 2),
            "emotional_intensity": round(self.emotional_intensity, 2),
            "publishability": round(self.publishability, 2),
            "staleness": round(self.staleness, 2),
        }


@dataclass
class SignalRecord:
    id: str
    event_id: str
    captured_at: str
    source: str
    source_id: str
    text: str
    signal_type: str
    topics: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    linked_projects: list[str] = field(default_factory=list)
    emotional_tone: str = "neutral"
    clarity_level: float = 0.0
    ambiguity_level: float = 0.0
    actionability: float = 0.0
    decision_readiness: float = 0.0
    recurrence_likelihood: float = 0.0
    dependencies: list[str] = field(default_factory=list)
    contradiction: bool = False
    sensitivity: str = "sensitive"
    status: str = "active"  # active, snoozed, pinned, irrelevant
    last_feedback_at: str = ""
    feedback_counts: dict[str, int] = field(default_factory=dict)
    scores: SignalScores = field(default_factory=SignalScores)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["scores"] = self.scores.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignalRecord":
        payload = dict(data)
        payload["scores"] = SignalScores(**payload.get("scores", {}))
        return cls(**{k: v for k, v in payload.items() if k in cls.__dataclass_fields__})


@dataclass
class FeedbackEvent:
    id: str
    signal_id: str
    action_type: str
    note: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OverrideEvent:
    id: str
    signal_id: str
    override_type: str
    expires_at: str = ""
    note: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score100(value: float) -> float:
    return round(clamp01(value) * 100.0, 2)


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 1]


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a.intersection(b)) / len(a.union(b))


class SignalMatcher:
    """Persistent deterministic signal matcher."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.events_path = data_dir / "signal_events.json"
        self.records_path = data_dir / "signal_records.json"
        self.feedback_path = data_dir / "signal_feedback.json"
        self.overrides_path = data_dir / "signal_overrides.json"
        self.links_path = data_dir / "signal_links.json"

        self._events: list[SignalEvent] = []
        self._records: list[SignalRecord] = []
        self._feedback: list[FeedbackEvent] = []
        self._overrides: list[OverrideEvent] = []

        self._load()

    # ----------------------------- persistence

    def _load(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._events = [SignalEvent(**row) for row in self._load_list(self.events_path)]
        self._records = [SignalRecord.from_dict(row) for row in self._load_list(self.records_path)]
        self._feedback = [FeedbackEvent(**row) for row in self._load_list(self.feedback_path)]
        self._overrides = [OverrideEvent(**row) for row in self._load_list(self.overrides_path)]

    def _save(self) -> None:
        self._save_list(self.events_path, [row.to_dict() for row in self._events])
        self._save_list(self.records_path, [row.to_dict() for row in self._records])
        self._save_list(self.feedback_path, [row.to_dict() for row in self._feedback])
        self._save_list(self.overrides_path, [row.to_dict() for row in self._overrides])

    @staticmethod
    def _load_list(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return data if isinstance(data, list) else []

    @staticmethod
    def _save_list(path: Path, payload: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # ----------------------------- ingestion

    def ingest(
        self,
        *,
        text: str,
        source: str,
        source_id: str = "",
        context: str = "",
        project: str = "",
        tags: list[str] | None = None,
        signal_type_hint: str = "",
    ) -> dict[str, Any] | None:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            return None

        event = SignalEvent(
            id=uuid.uuid4().hex[:14],
            captured_at=utc_now(),
            source=source,
            source_id=source_id,
            raw_text=cleaned,
            context=context.strip(),
            project=project.strip(),
            tags=[t.strip().lower() for t in (tags or []) if t.strip()],
        )
        self._events.append(event)

        rec = self._normalize(event, signal_type_hint=signal_type_hint)
        rec.scores = self._compute_scores(rec)
        self._records.append(rec)
        self._save()

        return {
            "event": event.to_dict(),
            "signal": rec.to_dict(),
        }

    def _normalize(self, event: SignalEvent, *, signal_type_hint: str = "") -> SignalRecord:
        inferred_type = self._infer_type(event.raw_text, source=event.source, signal_type_hint=signal_type_hint)
        topics = self._infer_topics(event.raw_text, base_tags=event.tags)
        tone, tone_score = self._infer_tone(event.raw_text)
        clarity = self._clarity(event.raw_text)
        ambiguity = self._ambiguity(event.raw_text)
        actionability = self._actionability(event.raw_text)
        decision_ready = self._decision_readiness(event.raw_text, clarity=clarity, ambiguity=ambiguity)
        dependencies = self._extract_dependencies(event.raw_text)
        recurrence = self._recurrence_likelihood(event.raw_text, topics=topics)
        contradiction = self._detect_contradiction(event.raw_text, topics=topics)
        sensitivity = self._sensitivity(event.raw_text, tags=event.tags)

        return SignalRecord(
            id=uuid.uuid4().hex[:14],
            event_id=event.id,
            captured_at=event.captured_at,
            source=event.source,
            source_id=event.source_id,
            text=event.raw_text,
            signal_type=inferred_type,
            topics=topics,
            tags=event.tags,
            linked_projects=[event.project] if event.project else [],
            emotional_tone=tone,
            clarity_level=round(clarity, 4),
            ambiguity_level=round(ambiguity, 4),
            actionability=round(actionability, 4),
            decision_readiness=round(decision_ready, 4),
            recurrence_likelihood=round(recurrence, 4),
            dependencies=dependencies,
            contradiction=contradiction,
            sensitivity=sensitivity,
            status="active",
            feedback_counts={},
            scores=SignalScores(emotional_intensity=score100(tone_score)),
        )

    def _infer_type(self, text: str, *, source: str, signal_type_hint: str = "") -> str:
        hint = signal_type_hint.strip().lower()
        if hint in VALID_TYPES:
            return hint

        source_hint = TYPE_HINT_MAP.get(source.strip().lower())
        tokens = set(tokenize(text))
        lowered = text.lower()

        if "?" in text or (tokens.intersection(QUESTION_TERMS)):
            if tokens.intersection(DECISION_TERMS):
                return "decision"
            return "question"
        if tokens.intersection(TENSION_TERMS):
            return "tension"
        if tokens.intersection(DECISION_TERMS):
            return "decision"
        if tokens.intersection(TASK_TERMS) or lowered.startswith("todo"):
            return "task"
        if tokens.intersection(IDEA_TERMS):
            if "content" in tokens or "newsletter" in tokens:
                return "content_seed"
            return "idea"
        if tokens.intersection(REFLECTION_TERMS):
            return "reflection"
        if source_hint:
            return source_hint
        return "thought"

    def _infer_topics(self, text: str, *, base_tags: list[str]) -> list[str]:
        tokens = tokenize(text)
        counts = Counter(token for token in tokens if len(token) > 3)
        topics = [token for token, _ in counts.most_common(4)]
        merged: list[str] = []
        for value in [*base_tags, *topics]:
            normalized = value.strip().lower().replace(" ", "_")
            if normalized and normalized not in merged:
                merged.append(normalized)
        return merged[:6]

    def _infer_tone(self, text: str) -> tuple[str, float]:
        lowered = text.lower()
        best = ("neutral", 0.2)
        for tone, keywords in TONE_KEYWORDS.items():
            hits = sum(1 for word in keywords if word in lowered)
            if hits > 0:
                intensity = clamp01(0.25 + hits * 0.2)
                if intensity > best[1]:
                    best = (tone, intensity)
        return best

    def _clarity(self, text: str) -> float:
        words = tokenize(text)
        if not words:
            return 0.0
        length_factor = clamp01(1.0 - abs(len(words) - 18) / 30)
        has_verb = 1.0 if any(word in ACTION_VERBS for word in words) else 0.0
        has_specificity = 1.0 if any(char.isdigit() for char in text) or ":" in text else 0.0
        return clamp01(0.55 * length_factor + 0.30 * has_verb + 0.15 * has_specificity)

    def _ambiguity(self, text: str) -> float:
        lowered = text.lower()
        hits = sum(1 for term in AMBIGUOUS_TERMS if term in lowered)
        question_noise = 0.2 if lowered.count("?") > 1 else 0.0
        return clamp01(hits * 0.2 + question_noise)

    def _actionability(self, text: str) -> float:
        words = set(tokenize(text))
        verb_score = clamp01(sum(1 for word in ACTION_VERBS if word in words) * 0.2)
        imperative_bonus = 0.2 if text.lower().startswith(("ship", "write", "fix", "review", "send")) else 0.0
        return clamp01(verb_score + imperative_bonus)

    def _decision_readiness(self, text: str, *, clarity: float, ambiguity: float) -> float:
        tokens = set(tokenize(text))
        decision_signal = 1.0 if tokens.intersection(DECISION_TERMS) else 0.3
        dependency_penalty = 0.2 if "depends on" in text.lower() or "waiting for" in text.lower() else 0.0
        return clamp01(0.55 * clarity + 0.30 * decision_signal - 0.35 * ambiguity - dependency_penalty)

    def _extract_dependencies(self, text: str) -> list[str]:
        lowered = text.lower()
        deps: list[str] = []
        patterns = [r"depends on ([a-z0-9_\-\s]{2,40})", r"waiting for ([a-z0-9_\-\s]{2,40})"]
        for pattern in patterns:
            for match in re.findall(pattern, lowered):
                dep = " ".join(match.split()).strip(" .,")
                if dep and dep not in deps:
                    deps.append(dep)
        return deps[:4]

    def _recurrence_likelihood(self, text: str, *, topics: list[str]) -> float:
        if not self._records:
            return 0.0
        tokens = set(tokenize(text))
        topic_set = set(topics)
        similar = 0
        window = self._records[-200:]
        for rec in window:
            overlap = jaccard(tokens, set(tokenize(rec.text)))
            topic_overlap = jaccard(topic_set, set(rec.topics))
            if overlap >= 0.35 or topic_overlap >= 0.45:
                similar += 1
        return clamp01(similar / 6.0)

    def _detect_contradiction(self, text: str, *, topics: list[str]) -> bool:
        lowered = text.lower()
        negation = any(term in lowered for term in ("stop", "drop", "cancel", "not doing", "avoid"))
        if not negation:
            return False
        topic_set = set(topics)
        for rec in reversed(self._records[-80:]):
            if rec.signal_type != "decision":
                continue
            if jaccard(topic_set, set(rec.topics)) >= 0.4:
                if not any(term in rec.text.lower() for term in ("stop", "drop", "cancel", "avoid")):
                    return True
        return False

    def _sensitivity(self, text: str, *, tags: list[str]) -> str:
        lowered = text.lower()
        tag_set = {t.lower() for t in tags}

        labels: list[str] = []
        if any(term in lowered for term in PRIVATE_TERMS) or "private" in tag_set:
            labels.append("private")
        if any(term in lowered for term in INTERNAL_TERMS) or "internal" in tag_set:
            labels.append("internal")
        if any(term in lowered for term in SENSITIVE_TERMS) or "sensitive" in tag_set:
            labels.append("sensitive")

        if not labels:
            labels.append("public_safe" if "public" in tag_set else "sensitive")

        return sorted(labels, key=lambda label: SENSITIVITY_RANK[label])[0]

    # ----------------------------- scoring + ranking

    def _compute_scores(self, rec: SignalRecord) -> SignalScores:
        now = datetime.now(UTC)
        captured = self._parse_dt(rec.captured_at)
        days_old = max(0.0, (now - captured).total_seconds() / 86400.0)

        recency = clamp01(math.exp(-days_old / 7.0))
        strategic = 1.0 if rec.linked_projects else (0.7 if rec.signal_type in {"decision", "task", "tension"} else 0.45)
        emotional = rec.scores.emotional_intensity / 100.0
        blockage = 1.0 if rec.signal_type in {"tension", "question"} or rec.dependencies else 0.2
        source_weight = SOURCE_WEIGHTS.get(rec.signal_type, 0.6)

        importance = score100(
            0.30 * source_weight
            + 0.20 * strategic
            + 0.15 * recency
            + 0.15 * rec.recurrence_likelihood
            + 0.10 * emotional
            + 0.10 * blockage
        )

        clarity_score = score100(0.50 * rec.clarity_level - 0.30 * rec.ambiguity_level + 0.20 * rec.actionability)
        decision_ready = score100(
            0.35 * rec.clarity_level
            + 0.25 * (1.0 - min(len(rec.dependencies), 3) / 3.0)
            + 0.20 * rec.recurrence_likelihood
            + 0.20 * rec.decision_readiness
        )
        action_ready = score100(
            0.40 * rec.actionability
            + 0.25 * rec.clarity_level
            + 0.20 * (1.0 - min(len(rec.dependencies), 3) / 3.0)
            + 0.15 * recency
        )

        recurrence = score100(rec.recurrence_likelihood)
        emotional_intensity = rec.scores.emotional_intensity

        public_safety = 1.0 if rec.sensitivity in {"public_safe", "public_ready"} else 0.0
        usefulness = clamp01((importance / 100.0 + action_ready / 100.0) / 2.0)
        originality = clamp01(1.0 - rec.recurrence_likelihood * 0.6)
        publishability = score100(0.45 * public_safety + 0.25 * usefulness + 0.20 * rec.clarity_level + 0.10 * originality)

        staleness = score100(clamp01(days_old / 14.0))

        return SignalScores(
            importance=importance,
            clarity=clarity_score,
            decision_readiness=decision_ready,
            action_readiness=action_ready,
            recurrence=recurrence,
            emotional_intensity=emotional_intensity,
            publishability=publishability,
            staleness=staleness,
        )

    def _rank_score(self, rec: SignalRecord) -> float:
        score = (
            0.40 * rec.scores.importance
            + 0.25 * rec.scores.action_readiness
            + 0.20 * rec.scores.decision_readiness
            + 0.10 * rec.scores.recurrence
            - 0.05 * rec.scores.staleness
        )

        # Explicit behavioural modifiers from feedback loop.
        acted = rec.feedback_counts.get("acted_on", 0)
        ignored = rec.feedback_counts.get("ignored", 0)
        reopened = rec.feedback_counts.get("reopened", 0)
        snoozed = rec.feedback_counts.get("snoozed", 0)
        marked_irrelevant = rec.feedback_counts.get("marked_irrelevant", 0)

        score += acted * 3.5
        score += reopened * 2.5
        score -= ignored * 3.0
        score -= snoozed * 1.8
        score -= marked_irrelevant * 10.0

        if rec.contradiction:
            score -= 6.0
        if rec.signal_type == "tension" and reopened > 0:
            score += 4.0  # unresolved tension boost

        return round(score, 2)

    def _time_horizon(self, rec: SignalRecord, rank_score: float) -> str:
        if rec.status == "pinned":
            return "now"
        if rec.status == "snoozed":
            return "later"

        if rec.scores.action_readiness >= 70 and rec.scores.importance >= 65:
            return "now"
        if rec.scores.importance >= 60 or rank_score >= 60:
            return "today"
        if rec.scores.importance >= 45 or rec.scores.recurrence >= 50:
            return "this_week"
        return "later"

    def build_ranked_output(self) -> dict[str, Any]:
        self._refresh_scores()

        active = [rec for rec in self._records if rec.status != "irrelevant"]
        ranked_items: list[dict[str, Any]] = []
        for rec in active:
            rank_score = self._rank_score(rec)
            horizon = self._time_horizon(rec, rank_score)
            ranked_items.append(
                {
                    "signal_id": rec.id,
                    "title": self._title(rec.text),
                    "signal_type": rec.signal_type,
                    "horizon": horizon,
                    "rank_score": rank_score,
                    "scores": rec.scores.to_dict(),
                    "topics": rec.topics,
                    "sensitivity": rec.sensitivity,
                    "explainability": self._explain(rec, rank_score=rank_score),
                    "next_action": self._next_action(rec),
                    "captured_at": rec.captured_at,
                }
            )

        ranked_items.sort(key=lambda item: item["rank_score"], reverse=True)

        top_priorities = self._build_top_priorities(ranked_items)
        decision_queue = [
            item for item in ranked_items
            if item["signal_type"] in {"decision", "question", "tension"}
            and item["scores"]["decision_readiness"] >= 55
        ][: QUEUE_LIMITS["decision_queue"]]
        action_ready_queue = [
            item for item in ranked_items
            if item["scores"]["action_readiness"] >= 55
        ][: QUEUE_LIMITS["action_ready_queue"]]

        recurring_patterns = self._recurring_patterns(active)
        unresolved_tensions = [
            item for item in ranked_items
            if item["signal_type"] == "tension" and item["scores"]["decision_readiness"] >= 45
        ][: QUEUE_LIMITS["unresolved_tensions"]]
        content_candidates = [
            item for item in ranked_items
            if item["signal_type"] in {"idea", "reflection", "content_seed", "thought"}
            and item["sensitivity"] in {"public_safe", "public_ready"}
            and item["scores"]["publishability"] >= 55
        ][: QUEUE_LIMITS["content_candidates"]]

        graph = self._build_graph(active)

        return {
            "generated_at": utc_now(),
            "top_priorities": top_priorities,
            "what_matters_now": [item for item in ranked_items if item["horizon"] == "now"][
                : QUEUE_LIMITS["what_matters_now"]
            ],
            "decision_queue": decision_queue,
            "action_ready_queue": action_ready_queue,
            "recurring_patterns": recurring_patterns,
            "unresolved_tensions": unresolved_tensions,
            "content_candidates": content_candidates,
            "signal_graph": graph,
            "limits": dict(QUEUE_LIMITS),
            "counts": {
                "signals_total": len(self._records),
                "signals_active": len(active),
                "ignored": len([rec for rec in self._records if rec.status == "irrelevant"]),
            },
        }

    def _refresh_scores(self) -> None:
        for rec in self._records:
            rec.scores = self._compute_scores(rec)
        self._save()

    def _build_top_priorities(self, ranked_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in ranked_items:
            if item["horizon"] not in {"now", "today"}:
                continue
            key = " ".join(tokenize(item["title"])[:4])
            if key in seen:
                continue
            seen.add(key)
            selected.append(
                {
                    "title": item["title"],
                    "why": item["explainability"]["why_it_surfaced"],
                    "action": item["next_action"],
                    "signal_id": item["signal_id"],
                    "rank_score": item["rank_score"],
                    "horizon": item["horizon"],
                }
            )
            if len(selected) >= 3:
                break
        return selected

    def _recurring_patterns(self, records: list[SignalRecord]) -> list[dict[str, Any]]:
        by_topic: dict[str, list[SignalRecord]] = defaultdict(list)
        for rec in records:
            if not rec.topics:
                continue
            by_topic[rec.topics[0]].append(rec)

        patterns: list[dict[str, Any]] = []
        for topic, topic_records in by_topic.items():
            if len(topic_records) < 2:
                continue
            unresolved = sum(1 for rec in topic_records if rec.feedback_counts.get("acted_on", 0) == 0)
            patterns.append(
                {
                    "topic": topic,
                    "count": len(topic_records),
                    "unresolved_count": unresolved,
                    "avg_importance": round(sum(rec.scores.importance for rec in topic_records) / len(topic_records), 2),
                    "sample_signals": [self._title(rec.text) for rec in topic_records[:3]],
                }
            )
        patterns.sort(key=lambda row: (row["unresolved_count"], row["avg_importance"], row["count"]), reverse=True)
        return patterns[: QUEUE_LIMITS["recurring_patterns"]]

    def _build_graph(self, records: list[SignalRecord]) -> dict[str, Any]:
        nodes = [
            {
                "id": rec.id,
                "type": rec.signal_type,
                "title": self._title(rec.text),
                "topics": rec.topics,
                "sensitivity": rec.sensitivity,
            }
            for rec in records[-120:]
        ]

        edges: list[dict[str, Any]] = []
        recent = records[-120:]
        for idx, left in enumerate(recent):
            left_tokens = set(tokenize(left.text))
            left_topics = set(left.topics)
            for right in recent[idx + 1:]:
                right_tokens = set(tokenize(right.text))
                right_topics = set(right.topics)
                similarity = max(jaccard(left_tokens, right_tokens), jaccard(left_topics, right_topics))
                if similarity < 0.45:
                    continue

                relation = "related_to"
                if left.signal_type == right.signal_type and similarity >= 0.6:
                    relation = "repeats"
                elif {left.signal_type, right.signal_type} == {"tension", "decision"}:
                    relation = "blocks"
                elif {left.signal_type, right.signal_type} == {"idea", "content_seed"}:
                    relation = "supports"

                edges.append(
                    {
                        "from": left.id,
                        "to": right.id,
                        "relation": relation,
                        "confidence": round(similarity, 2),
                    }
                )

        self.links_path.write_text(json.dumps(edges, indent=2), encoding="utf-8")
        return {"nodes": nodes, "edges": edges[:300]}

    # ----------------------------- explainability

    def _explain(self, rec: SignalRecord, *, rank_score: float) -> dict[str, Any]:
        contributors: list[str] = []
        if rec.scores.recurrence >= 60:
            contributors.append("recurring signal")
        if rec.scores.importance >= 65:
            contributors.append("high importance")
        if rec.scores.action_readiness >= 65:
            contributors.append("action-ready")
        if rec.scores.decision_readiness >= 65:
            contributors.append("decision-ready")
        if rec.signal_type == "tension":
            contributors.append("unresolved tension")

        lowered_confidence: list[str] = []
        if rec.scores.clarity < 45:
            lowered_confidence.append("low clarity")
        if rec.ambiguity_level > 0.45:
            lowered_confidence.append("high ambiguity")
        if rec.dependencies:
            lowered_confidence.append("has dependencies")
        if rec.contradiction:
            lowered_confidence.append("contradicts previous decision")

        missing: list[str] = []
        if rec.scores.decision_readiness < 65:
            missing.append("more decision framing")
        if rec.scores.action_readiness < 65:
            missing.append("clearer next action")
        if rec.dependencies:
            missing.append("dependency resolution")

        reason = (
            f"Surfaced because {', '.join(contributors[:3])}."
            if contributors
            else "Surfaced for baseline relevance in current context."
        )

        return {
            "why_it_surfaced": reason,
            "top_contributors": contributors[:4],
            "lowered_confidence": lowered_confidence[:4],
            "missing_for_readiness": missing[:4],
            "rank_score": rank_score,
        }

    # ----------------------------- feedback + overrides

    def apply_feedback(self, *, signal_id: str, action_type: str, note: str = "") -> dict[str, Any] | None:
        record = self._find_signal(signal_id)
        if record is None:
            return None

        action = action_type.strip().lower()
        allowed = {
            "acted_on",
            "ignored",
            "snoozed",
            "reopened",
            "converted_to_decision",
            "converted_to_action",
            "converted_to_content",
            "marked_irrelevant",
        }
        if action not in allowed:
            raise ValueError(f"Unsupported action_type '{action_type}'.")

        event = FeedbackEvent(
            id=uuid.uuid4().hex[:14],
            signal_id=signal_id,
            action_type=action,
            note=note.strip(),
            created_at=utc_now(),
        )
        self._feedback.append(event)

        record.feedback_counts[action] = record.feedback_counts.get(action, 0) + 1
        record.last_feedback_at = event.created_at

        if action == "marked_irrelevant":
            record.status = "irrelevant"
        elif action == "snoozed":
            record.status = "snoozed"
        elif action == "reopened" and record.status == "snoozed":
            record.status = "active"

        self._save()
        return {
            "feedback": event.to_dict(),
            "signal": record.to_dict(),
        }

    def apply_override(
        self,
        *,
        signal_id: str,
        override_type: str,
        note: str = "",
        expires_at: str = "",
    ) -> dict[str, Any] | None:
        record = self._find_signal(signal_id)
        if record is None:
            return None

        action = override_type.strip().lower()
        allowed = {
            "pin",
            "snooze",
            "mark_irrelevant",
            "mark_important",
            "convert_to_decision",
            "convert_to_action",
            "convert_to_content",
            "merge_related",
        }
        if action not in allowed:
            raise ValueError(f"Unsupported override_type '{override_type}'.")

        if action == "pin":
            record.status = "pinned"
        elif action == "snooze":
            record.status = "snoozed"
        elif action == "mark_irrelevant":
            record.status = "irrelevant"
        elif action == "mark_important":
            record.feedback_counts["manual_important"] = record.feedback_counts.get("manual_important", 0) + 1
        elif action == "convert_to_decision":
            record.signal_type = "decision"
        elif action == "convert_to_action":
            record.signal_type = "task"
            record.actionability = max(record.actionability, 0.7)
        elif action == "convert_to_content":
            record.signal_type = "content_seed"
            if record.sensitivity in {"private", "internal"}:
                record.sensitivity = "sensitive"

        event = OverrideEvent(
            id=uuid.uuid4().hex[:14],
            signal_id=signal_id,
            override_type=action,
            expires_at=expires_at,
            note=note.strip(),
            created_at=utc_now(),
        )
        self._overrides.append(event)
        self._save()
        return {
            "override": event.to_dict(),
            "signal": record.to_dict(),
        }

    def find_best_signal_id(self, text: str) -> str:
        tokens = set(tokenize(text))
        if not tokens:
            return ""
        best_id = ""
        best_score = 0.0
        for rec in self._records[-200:]:
            sim = jaccard(tokens, set(tokenize(rec.text)))
            if sim > best_score:
                best_score = sim
                best_id = rec.id
        return best_id if best_score >= 0.35 else ""

    # ----------------------------- query helpers

    def get_signal(self, signal_id: str) -> dict[str, Any] | None:
        rec = self._find_signal(signal_id)
        return rec.to_dict() if rec else None

    def list_signals(self, *, limit: int = 200) -> list[dict[str, Any]]:
        self._refresh_scores()
        return [rec.to_dict() for rec in reversed(self._records[-limit:])]

    def _find_signal(self, signal_id: str) -> SignalRecord | None:
        for rec in self._records:
            if rec.id == signal_id:
                return rec
        return None

    # ----------------------------- formatting helpers

    @staticmethod
    def _title(text: str) -> str:
        line = text.strip().split("\n", 1)[0].strip()
        if len(line) <= 88:
            return line
        return line[:85].rstrip() + "..."

    @staticmethod
    def _next_action(rec: SignalRecord) -> str:
        topic = rec.topics[0].replace("_", " ") if rec.topics else "this"
        if rec.signal_type == "decision":
            return f"Decide the next committed step for {topic}."
        if rec.signal_type == "question":
            return f"Answer the core open question on {topic}."
        if rec.signal_type == "tension":
            return f"Resolve the main blocker behind {topic}."
        if rec.signal_type == "task":
            return f"Execute the next concrete task for {topic}."
        if rec.signal_type in {"idea", "content_seed"}:
            return f"Draft one small experiment for {topic}."
        return f"Write one concrete next action for {topic}."

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        raw = str(value or "").strip()
        if not raw:
            return datetime.now(UTC)
        normalized = raw.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.now(UTC)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
