#!/usr/bin/env python3
"""Generate public-safe SimpliXio newsletter drafts from private source material.

Draft-only by design. No autopublish.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTOMATION_ROOT.parent
OUTPUT_ROOT = AUTOMATION_ROOT / "output" / "newsletters"
DRAFTS_DIR = OUTPUT_ROOT / "drafts"
APPROVED_DIR = OUTPUT_ROOT / "approved"
REJECTED_DIR = OUTPUT_ROOT / "rejected"
LOGS_DIR = OUTPUT_ROOT / "logs"

NEWSLETTER_MODES = {
    "personal-reflection",
    "product-builder-notes",
    "weekly-lessons",
    "technical-essay",
}

SOURCE_TYPES = {
    "thoughts",
    "notes",
    "decisions",
    "priority-feedback",
    "weekly-review",
    "decision-replay",
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{8,}\d")
LONG_NUMBER_RE = re.compile(r"\b\d{9,}\b")
URL_RE = re.compile(r"https?://\S+")
SECRET_RE = re.compile(r"\b(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,})\b")

CONFIDENTIAL_TERMS = {
    "confidential",
    "sensitive",
    "internal",
    "internal only",
    "do-not-publish",
    "do not publish",
    "private",
    "client",
    "workplace",
    "nda",
    "password",
    "secret",
    "token",
    "api key",
    "credential",
    "visa",
    "immigration",
    "health",
    "salary",
    "revenue",
    "bank account",
    "credit card",
}

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "for",
    "in",
    "on",
    "with",
    "this",
    "that",
    "from",
    "into",
    "about",
    "what",
    "why",
    "when",
    "where",
    "today",
    "week",
    "simpliXio",
    "simplixio",
}


@dataclass
class SourceItem:
    source_id: str
    source_type: str
    source_file: str
    date: str
    text: str
    tags: list[str] = field(default_factory=list)


@dataclass
class SanitizedItem:
    source_id: str
    source_type: str
    source_file: str
    date: str
    text: str
    tags: list[str] = field(default_factory=list)
    redactions: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def ensure_dirs(output_root: Path | None = None) -> None:
    root = output_root or OUTPUT_ROOT
    for path in (root / "drafts", root / "approved", root / "rejected", root / "logs"):
        path.mkdir(parents=True, exist_ok=True)


def parse_iso_datetime(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_iso_date(value: str) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def default_data_dirs() -> list[Path]:
    return [REPO_ROOT / ".cortexos_local", Path.home() / ".cortexos"]


def pick_data_dir() -> Path | None:
    for directory in default_data_dirs():
        if directory.exists():
            return directory
    return None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def in_range(item_date: date | None, start_date: date, end_date: date) -> bool:
    if item_date is None:
        return False
    return start_date <= item_date <= end_date


def normalize_tag_set(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value.strip()}


def parse_csv_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_period_range(
    *,
    period: str,
    from_date: str,
    to_date: str,
    today: date,
) -> tuple[date, date]:
    if period == "custom":
        start = parse_iso_date(from_date)
        end = parse_iso_date(to_date)
        if start is None or end is None:
            raise ValueError("Custom period requires valid --from and --to dates (YYYY-MM-DD).")
    elif period == "daily":
        start = today
        end = today
    elif period == "weekly":
        end = today
        start = end - timedelta(days=6)
    elif period == "monthly":
        end = today
        start = end - timedelta(days=29)
    else:
        raise ValueError(f"Unsupported period: {period}")

    if start > end:
        raise ValueError("--from date must be before or equal to --to date.")
    return start, end


def load_thoughts_and_notes(
    data_dir: Path,
    start_date: date,
    end_date: date,
) -> list[SourceItem]:
    path = data_dir / "knowledge_notes.json"
    if not path.exists():
        return []
    raw = load_json(path)
    if not isinstance(raw, list):
        return []

    items: list[SourceItem] = []
    for idx, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        if bool(row.get("archived", False)):
            continue
        created_raw = str(row.get("created_at") or row.get("createdAt") or "")
        created_dt = parse_iso_datetime(created_raw)
        if not in_range(created_dt.date() if created_dt else None, start_date, end_date):
            continue

        title = str(row.get("title", "")).strip()
        insight = str(row.get("insight", "")).strip()
        implication = str(row.get("implication", "")).strip()
        action = str(row.get("action", "")).strip()
        tags = [str(tag).strip() for tag in row.get("tags", []) if str(tag).strip()]
        text_parts = [part for part in (title, insight, implication, action) if part]
        text = " ".join(text_parts).strip()
        if not text:
            continue

        note_id = str(row.get("id", "")).strip() or f"note-{idx}"
        items.append(
            SourceItem(
                source_id=note_id,
                source_type="thoughts",
                source_file=str(path),
                date=created_dt.date().isoformat() if created_dt else "",
                text=text,
                tags=tags,
            )
        )
    return items


def load_decisions(
    data_dir: Path,
    start_date: date,
    end_date: date,
) -> list[SourceItem]:
    items: list[SourceItem] = []

    decisions_path = data_dir / "decisions.json"
    if decisions_path.exists():
        raw = load_json(decisions_path)
        if isinstance(raw, list):
            for idx, row in enumerate(raw):
                if not isinstance(row, dict):
                    continue
                created_dt = parse_iso_datetime(str(row.get("created_at", "")))
                if not in_range(created_dt.date() if created_dt else None, start_date, end_date):
                    continue
                decision = str(row.get("decision", "")).strip()
                reason = str(row.get("reason", "")).strip()
                outcome = str(row.get("outcome", "")).strip()
                text = " ".join(part for part in (decision, reason, outcome) if part).strip()
                if not text:
                    continue
                source_id = str(row.get("id", "")).strip() or f"decision-{idx}"
                items.append(
                    SourceItem(
                        source_id=source_id,
                        source_type="decisions",
                        source_file=str(decisions_path),
                        date=created_dt.date().isoformat() if created_dt else "",
                        text=text,
                        tags=[],
                    )
                )

    for path in sorted(data_dir.glob("decision_*.json")):
        payload = load_json(path)
        if not isinstance(payload, dict):
            continue
        day = parse_iso_date(str(payload.get("date", "")))
        if not in_range(day, start_date, end_date):
            continue
        priorities = payload.get("priorities", [])
        if not isinstance(priorities, list):
            continue
        for idx, row in enumerate(priorities[:3]):
            if not isinstance(row, dict):
                continue
            title = str(row.get("title", "")).strip()
            why = str(row.get("why_it_matters", "")).strip()
            action = str(row.get("next_step", "")).strip()
            text = " ".join(part for part in (title, why, action) if part).strip()
            if not text:
                continue
            source_id = f"{path.stem}-priority-{idx + 1}"
            items.append(
                SourceItem(
                    source_id=source_id,
                    source_type="decisions",
                    source_file=str(path),
                    date=day.isoformat() if day else "",
                    text=text,
                    tags=[],
                )
            )
    return items


def load_priority_feedback(
    data_dir: Path,
    start_date: date,
    end_date: date,
) -> list[SourceItem]:
    path = data_dir / "working_memory.json"
    if not path.exists():
        return []

    payload = load_json(path)
    if not isinstance(payload, dict):
        return []

    day = parse_iso_date(str(payload.get("date", "")))
    if day is None:
        return []
    if not in_range(day, start_date, end_date):
        return []

    raw_notes = payload.get("temporary_notes", [])
    if not isinstance(raw_notes, list):
        return []

    items: list[SourceItem] = []
    for idx, value in enumerate(raw_notes):
        note = str(value).strip()
        if not note:
            continue
        source_id = f"feedback-{day.isoformat()}-{idx + 1}"
        items.append(
            SourceItem(
                source_id=source_id,
                source_type="priority-feedback",
                source_file=str(path),
                date=day.isoformat(),
                text=note,
                tags=["feedback"],
            )
        )
    return items


def load_weekly_review_output(
    start_date: date,
    end_date: date,
) -> list[SourceItem]:
    path = AUTOMATION_ROOT / "output" / "weekly_review" / "latest.json"
    if not path.exists():
        return []
    payload = load_json(path)
    if not isinstance(payload, dict):
        return []

    week_end = parse_iso_date(str(payload.get("week_end", "")))
    if week_end is not None and not in_range(week_end, start_date, end_date):
        return []

    summary = str(payload.get("summary", "")).strip()
    recommendations = payload.get("recommendations", [])
    rec_text = " ".join(str(item).strip() for item in recommendations if str(item).strip())
    body = " ".join(part for part in (summary, rec_text) if part).strip()
    if not body:
        return []

    source_day = week_end.isoformat() if week_end else end_date.isoformat()
    return [
        SourceItem(
            source_id=f"weekly-review-{source_day}",
            source_type="weekly-review",
            source_file=str(path),
            date=source_day,
            text=body,
            tags=["weekly-review"],
        )
    ]


def load_decision_replay_output(
    start_date: date,
    end_date: date,
) -> list[SourceItem]:
    path = AUTOMATION_ROOT / "output" / "decision_replay" / "latest.json"
    if not path.exists():
        return []
    payload = load_json(path)
    if not isinstance(payload, dict):
        return []

    day = parse_iso_date(str(payload.get("date", "")))
    if day is not None and not in_range(day, start_date, end_date):
        return []

    summary = str(payload.get("summary", "")).strip()
    priorities = payload.get("final_priorities", [])
    priority_lines: list[str] = []
    if isinstance(priorities, list):
        for row in priorities[:3]:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title", "")).strip()
            why = str(row.get("why", "")).strip()
            action = str(row.get("action", "")).strip()
            text = " ".join(part for part in (title, why, action) if part).strip()
            if text:
                priority_lines.append(text)

    body = " ".join([summary, *priority_lines]).strip()
    if not body:
        return []

    source_day = day.isoformat() if day else end_date.isoformat()
    return [
        SourceItem(
            source_id=f"decision-replay-{source_day}",
            source_type="decision-replay",
            source_file=str(path),
            date=source_day,
            text=body,
            tags=["decision-replay"],
        )
    ]


def collect_source_items(
    *,
    data_dir: Path,
    start_date: date,
    end_date: date,
    source_types: set[str],
) -> list[SourceItem]:
    items: list[SourceItem] = []

    if "thoughts" in source_types or "notes" in source_types:
        items.extend(load_thoughts_and_notes(data_dir, start_date, end_date))
    if "decisions" in source_types:
        items.extend(load_decisions(data_dir, start_date, end_date))
    if "priority-feedback" in source_types:
        items.extend(load_priority_feedback(data_dir, start_date, end_date))
    if "weekly-review" in source_types:
        items.extend(load_weekly_review_output(start_date, end_date))
    if "decision-replay" in source_types:
        items.extend(load_decision_replay_output(start_date, end_date))

    return items


def apply_selection_filters(
    items: list[SourceItem],
    *,
    source_ids: set[str],
    tags: set[str],
    keywords: set[str],
) -> list[SourceItem]:
    if not source_ids and not tags and not keywords:
        return items

    filtered: list[SourceItem] = []
    for item in items:
        item_tags = normalize_tag_set(item.tags)
        text_lower = item.text.lower()
        source_id_match = item.source_id in source_ids if source_ids else True

        tag_match = bool(tags.intersection(item_tags)) if tags else True
        keyword_match = any(keyword in text_lower for keyword in keywords) if keywords else True
        if source_id_match and tag_match and keyword_match:
            filtered.append(item)
    return filtered


def apply_redactions(text: str) -> tuple[str, list[str]]:
    redactions: list[str] = []
    value = text

    if EMAIL_RE.search(value):
        redactions.append("email")
        value = EMAIL_RE.sub("[personal detail removed]", value)
    if PHONE_RE.search(value):
        redactions.append("phone")
        value = PHONE_RE.sub("[personal detail removed]", value)
    if LONG_NUMBER_RE.search(value):
        redactions.append("long-number")
        value = LONG_NUMBER_RE.sub("[personal detail removed]", value)
    if URL_RE.search(value):
        redactions.append("url")
        value = URL_RE.sub("[private link removed]", value)
    if SECRET_RE.search(value):
        redactions.append("credential")
        value = SECRET_RE.sub("[confidential detail removed]", value)

    return value.strip(), redactions


def detect_blockers(text: str) -> list[str]:
    lowered = text.lower()
    blockers = [term for term in CONFIDENTIAL_TERMS if term in lowered]
    return sorted(set(blockers))


def sanitize_source_item(item: SourceItem) -> SanitizedItem:
    redacted, redactions = apply_redactions(item.text)
    blockers = detect_blockers(redacted)
    clean_text = redacted
    if blockers:
        clean_text = ""

    return SanitizedItem(
        source_id=item.source_id,
        source_type=item.source_type,
        source_file=item.source_file,
        date=item.date,
        text=clean_text,
        tags=item.tags,
        redactions=redactions,
        blocked_reasons=blockers,
    )


def mode_subtitle(mode: str) -> str:
    mapping = {
        "personal-reflection": "A practical reflection from real notes and decisions.",
        "product-builder-notes": "Real product lessons from building SimpliXio.",
        "weekly-lessons": "What this week taught me about deciding what matters.",
        "technical-essay": "A focused technical draft from real engineering decisions.",
    }
    return mapping.get(mode, mapping["weekly-lessons"])


def mode_cta(mode: str) -> str:
    mapping = {
        "personal-reflection": "If this helped, reply with one thing you are choosing to ignore this week.",
        "product-builder-notes": "If you build products, share how you choose your top 3 priorities each day.",
        "weekly-lessons": "Try this for one week: 3 priorities, why each matters, and one next action.",
        "technical-essay": "If you want more technical notes, follow the next SimpliXio builder update.",
    }
    return mapping.get(mode, mapping["weekly-lessons"])


def title_options(mode: str, period_label: str, keywords: list[str]) -> list[str]:
    top = keywords[0] if keywords else "Decision Quality"
    return (
        [
            f"From Noise to Action ({period_label})",
            f"Three Priorities, Better Outcomes: {top}",
            "What I Learned While Building SimpliXio This Week",
        ]
        if mode != "technical-essay"
        else [
            f"Engineering Decision Replay ({period_label})",
            f"Building a Calm Decision System Around {top}",
            "Technical Notes from SimpliXio",
        ]
    )


def group_items(items: list[SanitizedItem], source_type: str, limit: int = 5) -> list[str]:
    lines = [item.text for item in items if item.source_type == source_type and item.text]
    return lines[:limit]


def top_keywords(items: list[SanitizedItem], limit: int = 8) -> list[str]:
    counter: Counter[str] = Counter()
    for item in items:
        for token in re.findall(r"[A-Za-z0-9]+", item.text.lower()):
            if len(token) < 4:
                continue
            if token in STOPWORDS:
                continue
            counter[token] += 1
    return [word for word, _ in counter.most_common(limit)]


def build_sections(
    *,
    mode: str,
    start_date: date,
    end_date: date,
    items: list[SanitizedItem],
) -> dict[str, Any]:
    keywords = top_keywords(items)
    titles = title_options(mode, f"{start_date.isoformat()} to {end_date.isoformat()}", keywords)
    subtitle = mode_subtitle(mode)

    thought_lines = group_items(items, "thoughts", limit=6)
    decision_lines = group_items(items, "decisions", limit=6)
    replay_lines = group_items(items, "decision-replay", limit=3)
    review_lines = group_items(items, "weekly-review", limit=3)

    opening_hook = (
        "This draft comes from real captured thoughts and decisions. "
        "It is cleaned for public safety without flattening the original intent."
    )

    main_idea_lines = thought_lines[:3] + decision_lines[:2]
    what_i_noticed = decision_lines[:4] + replay_lines[:2]
    what_this_means = review_lines[:2]
    if not what_this_means and keywords:
        what_this_means = [
            f"Recurring themes this period: {', '.join(keywords[:4])}.",
            "Reducing noise still drives better execution than collecting more input.",
        ]

    practical_takeaway = "Pick 3 priorities, write why each matters, then commit one concrete next action."
    closing_thought = (
        "The hard part is not finding more information. The hard part is deciding what deserves attention."
    )
    main_newsletter_body = (main_idea_lines + what_i_noticed)[:8]
    key_lessons = what_this_means[:4]

    return {
        "title_options": titles,
        "subtitle": subtitle,
        "opening_hook": opening_hook,
        "main_idea_lines": main_idea_lines,
        "what_i_noticed": what_i_noticed,
        "what_this_means": what_this_means,
        "main_newsletter_body": main_newsletter_body,
        "key_lessons": key_lessons,
        "practical_takeaway": practical_takeaway,
        "optional_cta": mode_cta(mode),
        "closing_thought": closing_thought,
        "keywords": keywords,
    }


def build_safety_report(items: list[SanitizedItem]) -> dict[str, Any]:
    blocked = [item for item in items if item.blocked_reasons]
    redacted = [item for item in items if item.redactions]

    blocked_reasons = Counter(reason for item in blocked for reason in item.blocked_reasons)
    redaction_types = Counter(tag for item in redacted for tag in item.redactions)

    raw_sensitive_found = any(EMAIL_RE.search(item.text) or PHONE_RE.search(item.text) for item in items if item.text)
    safe_to_publish = len(blocked) == 0 and not raw_sensitive_found

    remaining_concerns: list[str] = []
    if blocked:
        remaining_concerns.append("Confidential indicators were detected in source material.")
    if raw_sensitive_found:
        remaining_concerns.append("Potential personal identifiers may remain.")

    recommendation = (
        "Manual review recommended before publishing."
        if not safe_to_publish
        else "No critical safety blockers detected."
    )

    return {
        "safe_to_publish": safe_to_publish,
        "sensitive_items_removed": [
            {"item_type": reason, "count": count, "reason": "Matched confidentiality policy"}
            for reason, count in blocked_reasons.items()
        ],
        "redactions_applied": [{"item_type": kind, "count": count} for kind, count in redaction_types.items()],
        "remaining_concerns": remaining_concerns,
        "recommendation": recommendation,
    }


def build_quality_scores(
    *,
    mode: str,
    sections: dict[str, Any],
    safety_report: dict[str, Any],
    sanitized_items: list[SanitizedItem],
) -> dict[str, int]:
    authenticity = min(100, 50 + len(sections.get("main_idea_lines", [])) * 8)
    clarity = 90 if sections.get("practical_takeaway") else 60
    usefulness = 85 if sections.get("what_this_means") else 60
    privacy_safety = 95 if safety_report.get("safe_to_publish") else 55
    public_value = min(95, 55 + len(sections.get("keywords", [])) * 5)

    alignment_terms = {"decision", "priority", "action", "noise", "matters"}
    combined = " ".join(item.text.lower() for item in sanitized_items if item.text)
    alignment_hits = sum(1 for term in alignment_terms if term in combined)
    alignment = min(100, 55 + alignment_hits * 10)

    return {
        "authenticity": authenticity,
        "clarity": clarity,
        "usefulness": usefulness,
        "privacy_safety": privacy_safety,
        "public_value": public_value,
        "alignment": alignment,
        "overall": round((authenticity + clarity + usefulness + privacy_safety + public_value + alignment) / 6),
    }


def render_markdown(
    *,
    sections: dict[str, Any],
    safety_report: dict[str, Any],
    quality_scores: dict[str, int],
) -> str:
    title_options = sections["title_options"]
    title = title_options[0]

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(sections["subtitle"])
    lines.append("")
    lines.append(sections["opening_hook"])
    lines.append("")

    lines.append("## Title options")
    lines.append("")
    for option in title_options:
        lines.append(f"- {option}")
    lines.append("")

    lines.append("## Main idea")
    lines.append("")
    if sections["main_idea_lines"]:
        for line in sections["main_idea_lines"]:
            lines.append(f"- {line}")
    else:
        lines.append("- No main ideas selected from safe source material.")
    lines.append("")

    lines.append("## What I noticed")
    lines.append("")
    if sections["what_i_noticed"]:
        for line in sections["what_i_noticed"]:
            lines.append(f"- {line}")
    else:
        lines.append("- No notable patterns were extracted safely.")
    lines.append("")

    lines.append("## What this means")
    lines.append("")
    for line in sections["what_this_means"]:
        lines.append(f"- {line}")
    lines.append("")

    lines.append("## Main newsletter body")
    lines.append("")
    if sections["main_newsletter_body"]:
        for line in sections["main_newsletter_body"]:
            lines.append(f"- {line}")
    else:
        lines.append("- No public-safe body content was extracted.")
    lines.append("")

    lines.append("## Key lessons")
    lines.append("")
    if sections["key_lessons"]:
        for line in sections["key_lessons"]:
            lines.append(f"- {line}")
    else:
        lines.append("- No key lessons were extracted safely.")
    lines.append("")

    lines.append("## Practical takeaway")
    lines.append("")
    lines.append(sections["practical_takeaway"])
    lines.append("")

    lines.append("## Optional CTA")
    lines.append("")
    lines.append(sections["optional_cta"])
    lines.append("")

    lines.append("## Closing thought")
    lines.append("")
    lines.append(sections["closing_thought"])
    lines.append("")

    lines.append("## Safety Report")
    lines.append("")
    lines.append(f"- Safe to publish: {'yes' if safety_report['safe_to_publish'] else 'no'}")
    lines.append("- Sensitive items removed:")
    if safety_report["sensitive_items_removed"]:
        for item in safety_report["sensitive_items_removed"]:
            lines.append(f"  - {item['item_type']} ({item['count']}): {item['reason']}")
    else:
        lines.append("  - none")
    lines.append("- Remaining concerns:")
    if safety_report["remaining_concerns"]:
        for concern in safety_report["remaining_concerns"]:
            lines.append(f"  - {concern}")
    else:
        lines.append("  - none")
    lines.append(f"- Recommendation: {safety_report['recommendation']}")
    lines.append("")

    lines.append("## Redaction Report")
    lines.append("")
    if safety_report["redactions_applied"]:
        for item in safety_report["redactions_applied"]:
            lines.append(f"- {item['item_type']}: {item['count']}")
    else:
        lines.append("- No redactions applied.")
    lines.append("")

    lines.append("## Quality Scores")
    lines.append("")
    for key in ("authenticity", "clarity", "usefulness", "privacy_safety", "public_value", "alignment", "overall"):
        lines.append(f"- {key.replace('_', ' ')}: {quality_scores[key]}")
    lines.append("")

    return "\n".join(lines)


def render_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_lines = [
        "<!doctype html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8' />",
        "  <meta name='viewport' content='width=device-width, initial-scale=1' />",
        "  <title>SimpliXio Newsletter Draft</title>",
        "  <style>",
        (
            "    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; "
            "background: #0b1220; color: #eef2ff; max-width: 900px; margin: 40px auto; "
            "padding: 0 20px; line-height: 1.6; }"
        ),
        "    h1, h2 { color: #ffffff; }",
        "    ul { padding-left: 20px; }",
        "    p, li { color: #d8e1f7; }",
        "  </style>",
        "</head>",
        "<body>",
    ]
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif stripped == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br/>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{stripped}</p>")
    if in_list:
        html_lines.append("</ul>")
    html_lines.extend(["</body>", "</html>"])
    return "\n".join(html_lines)


def write_outputs(
    *,
    output_root: Path,
    status: str,
    markdown_text: str,
    html_text: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    ensure_dirs(output_root)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    basename = f"newsletter-{stamp}"

    if status in {"draft", "exported"}:
        target_dir = output_root / "drafts"
    elif status == "approved":
        target_dir = output_root / "approved"
    else:
        target_dir = output_root / "rejected"

    md_path = target_dir / f"{basename}.md"
    html_path = target_dir / f"{basename}.html"
    log_path = output_root / "logs" / f"{basename}.json"

    md_path.write_text(markdown_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    latest_json = output_root / "latest.json"
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "markdown": str(md_path),
        "html": str(html_path),
        "log": str(log_path),
        "latest": str(latest_json),
    }


def run_generation(
    *,
    period: str = "weekly",
    from_date: str = "",
    to_date: str = "",
    mode: str = "weekly-lessons",
    output: str = "",
    strict_safety: bool = True,
    sources: str = "",
    source_ids: str = "",
    tags: str = "",
    keywords: str = "",
) -> dict[str, Any]:
    if mode not in NEWSLETTER_MODES:
        raise ValueError(f"Unsupported mode '{mode}'. Expected one of {sorted(NEWSLETTER_MODES)}.")

    output_root = Path(output).expanduser().resolve() if output else OUTPUT_ROOT
    ensure_dirs(output_root)

    data_dir = pick_data_dir()
    if data_dir is None:
        payload = {
            "status": "rejected",
            "generated_at": utc_now().isoformat(),
            "reason": "no_data_directory",
            "safe_to_publish": False,
        }
        outputs = write_outputs(
            output_root=output_root,
            status="rejected",
            markdown_text="# SimpliXio Newsletter Draft\n\nNo data directory was found for source material.\n",
            html_text=(
                "<html><body><h1>SimpliXio Newsletter Draft</h1>"
                "<p>No data directory was found for source material.</p></body></html>"
            ),
            payload=payload,
        )
        payload["outputs"] = outputs
        return payload

    now = utc_now().date()
    start_date, end_date = build_period_range(
        period=period,
        from_date=from_date,
        to_date=to_date,
        today=now,
    )

    source_set = set(parse_csv_list(sources)) if sources.strip() else set(SOURCE_TYPES)
    invalid_sources = source_set.difference(SOURCE_TYPES)
    if invalid_sources:
        raise ValueError(f"Unsupported sources: {sorted(invalid_sources)}")

    selected_tags = normalize_tag_set(parse_csv_list(tags))
    selected_keywords = normalize_tag_set(parse_csv_list(keywords))
    selected_source_ids = {value.strip() for value in parse_csv_list(source_ids)}

    source_items = collect_source_items(
        data_dir=data_dir,
        start_date=start_date,
        end_date=end_date,
        source_types=source_set,
    )
    source_items = apply_selection_filters(
        source_items,
        source_ids=selected_source_ids,
        tags=selected_tags,
        keywords=selected_keywords,
    )

    sanitized = [sanitize_source_item(item) for item in source_items]
    usable = [item for item in sanitized if item.text]

    safety_report = build_safety_report(sanitized)
    quality_scores = {
        "authenticity": 0,
        "clarity": 0,
        "usefulness": 0,
        "privacy_safety": 0,
        "public_value": 0,
        "alignment": 0,
        "overall": 0,
    }

    if not usable:
        status = "rejected"
        reason = "no_public_safe_items"
        markdown_text = (
            "# SimpliXio Newsletter Draft\n\nNo public-safe source material was available for this period.\n"
        )
        html_text = (
            "<html><body><h1>SimpliXio Newsletter Draft</h1>"
            "<p>No public-safe source material was available for this period.</p></body></html>"
        )
    else:
        sections = build_sections(
            mode=mode,
            start_date=start_date,
            end_date=end_date,
            items=usable,
        )
        quality_scores = build_quality_scores(
            mode=mode,
            sections=sections,
            safety_report=safety_report,
            sanitized_items=usable,
        )
        markdown_text = render_markdown(
            sections=sections,
            safety_report=safety_report,
            quality_scores=quality_scores,
        )
        html_text = render_html(markdown_text)

        safe_to_publish = bool(safety_report["safe_to_publish"])
        if strict_safety and not safe_to_publish:
            status = "needs_review"
            reason = "strict_safety_blocked"
        else:
            status = "draft"
            reason = "ok"

    payload = {
        "status": status,
        "generated_at": utc_now().isoformat(),
        "period": period,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "mode": mode,
        "strict_safety": strict_safety,
        "safe_to_publish": bool(safety_report["safe_to_publish"]),
        "reason": reason,
        "source_data_dir": str(data_dir),
        "source_ids": [item.source_id for item in sanitized],
        "source_types_used": sorted({item.source_type for item in sanitized}),
        "source_count_total": len(sanitized),
        "source_count_usable": len(usable),
        "selected_filters": {
            "sources": sorted(source_set),
            "source_ids": sorted(selected_source_ids),
            "tags": sorted(selected_tags),
            "keywords": sorted(selected_keywords),
        },
        "safety_report": safety_report,
        "redaction_report": {
            "total_items_redacted": sum(1 for item in sanitized if item.redactions),
            "total_items_blocked": sum(1 for item in sanitized if item.blocked_reasons),
            "items": [
                {
                    "source_id": item.source_id,
                    "source_type": item.source_type,
                    "redactions": item.redactions,
                    "blocked_reasons": item.blocked_reasons,
                }
                for item in sanitized
                if item.redactions or item.blocked_reasons
            ],
        },
        "quality_scores": quality_scores,
    }

    payload["outputs"] = write_outputs(
        output_root=output_root,
        status=status,
        markdown_text=markdown_text,
        html_text=html_text,
        payload=payload,
    )
    return payload


def run_legacy(days: int = 7) -> dict[str, Any]:
    """Compatibility path for older build_public_newsletter calls."""
    if days <= 1:
        period = "daily"
    elif days >= 28:
        period = "monthly"
    else:
        period = "weekly"
    return run_generation(period=period, strict_safety=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a public-safe SimpliXio newsletter draft.")
    parser.add_argument("--period", choices=["daily", "weekly", "monthly", "custom"], default="weekly")
    parser.add_argument("--from", dest="from_date", default="", help="Start date (YYYY-MM-DD) for custom range.")
    parser.add_argument("--to", dest="to_date", default="", help="End date (YYYY-MM-DD) for custom range.")
    parser.add_argument("--mode", choices=sorted(NEWSLETTER_MODES), default="weekly-lessons")
    parser.add_argument("--output", default="", help="Output root directory (default: output/newsletters).")
    parser.add_argument("--sources", default="", help="Comma-separated source types.")
    parser.add_argument("--source-ids", default="", help="Comma-separated source IDs to include.")
    parser.add_argument("--tags", default="", help="Comma-separated tags filter.")
    parser.add_argument("--keywords", default="", help="Comma-separated keyword filter.")
    parser.set_defaults(strict_safety=True)
    parser.add_argument(
        "--strict-safety",
        dest="strict_safety",
        action="store_true",
        help="Enable strict safety mode (unsafe drafts become needs_review).",
    )
    parser.add_argument(
        "--no-strict-safety",
        dest="strict_safety",
        action="store_false",
        help="Disable strict safety mode (unsafe drafts remain draft).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_generation(
        period=args.period,
        from_date=args.from_date,
        to_date=args.to_date,
        mode=args.mode,
        output=args.output,
        strict_safety=args.strict_safety,
        sources=args.sources,
        source_ids=args.source_ids,
        tags=args.tags,
        keywords=args.keywords,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
