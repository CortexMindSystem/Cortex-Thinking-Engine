#!/usr/bin/env python3
"""Score lead fit for SimpliXio (0-100), then classify fit/not_fit."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from acquisition_crm import (
    AUTOMATION_ROOT,
    OUTPUT_DIR,
    connect,
    init_db,
    list_leads_for_scoring,
    update_lead_score,
)


ROLE_TERMS = {
    "founder": 20,
    "operator": 18,
    "product engineer": 20,
    "engineer": 12,
    "builder": 12,
    "indie hacker": 16,
    "developer": 10,
    "cto": 18,
    "head of product": 18,
    "product manager": 14,
}

PAIN_TERMS = {
    "information overload": 20,
    "decision fatigue": 20,
    "priorit": 16,
    "workflow": 10,
    "noise": 14,
    "context": 12,
    "focus": 10,
    "signal": 10,
    "decision loop": 18,
    "decision quality": 18,
}

PROJECT_ACTIVITY_TERMS = {
    "launch": 12,
    "released": 12,
    "shipping": 10,
    "beta": 8,
    "changelog": 8,
    "open source": 6,
    "repo": 6,
    "roadmap": 8,
    "iteration": 8,
    "release notes": 10,
}

NEGATIVE_TERMS = {
    "celebrity": -20,
    "movie": -18,
    "music": -14,
    "gaming": -12,
    "giveaway": -18,
}


def load_threshold() -> int:
    load_dotenv(AUTOMATION_ROOT / ".env")
    return int(os.getenv("ACQ_FIT_THRESHOLD", "55"))


def load_candidate_gap() -> int:
    load_dotenv(AUTOMATION_ROOT / ".env")
    return int(os.getenv("ACQ_CANDIDATE_GAP", "12"))


def score_lead(title: str, source: str, payload: dict[str, Any]) -> tuple[int, str]:
    text = " ".join(
        [
            title or "",
            source or "",
            str(payload.get("excerpt", "") or ""),
            " ".join([str(x) for x in payload.get("tags", [])]),
            str(payload.get("raw", {})),
        ]
    ).lower()

    score = 0
    reasons: list[str] = []

    for term, points in ROLE_TERMS.items():
        if term in text:
            score += points
            reasons.append(term)

    for term, points in PAIN_TERMS.items():
        if term in text:
            score += points
            reasons.append(term)

    for term, points in PROJECT_ACTIVITY_TERMS.items():
        if term in text:
            score += points
            reasons.append(term)

    for term, penalty in NEGATIVE_TERMS.items():
        if term in text:
            score += penalty
            reasons.append(f"neg:{term}")

    raw = payload.get("raw", {}) if isinstance(payload, dict) else {}
    if not isinstance(raw, dict):
        raw = {}

    # Source-level weighting
    if source in {"github", "hacker_news"}:
        score += 6
    if source == "rss":
        score += 2

    # Lightweight source-specific activity boosts
    if source == "github":
        stars = int(raw.get("stars", 0) or 0)
        forks = int(raw.get("forks", 0) or 0)
        if stars >= 500:
            score += 10
            reasons.append("github:high_stars")
        elif stars >= 100:
            score += 6
            reasons.append("github:solid_stars")
        if forks >= 50:
            score += 4
            reasons.append("github:forks")

    if source == "hacker_news":
        points = int(raw.get("points", 0) or 0)
        comments = int(raw.get("num_comments", 0) or 0)
        if points >= 100:
            score += 8
            reasons.append("hn:high_points")
        if comments >= 40:
            score += 6
            reasons.append("hn:discussion")

    if source.startswith("simplixio_"):
        score -= 15  # internal artifacts are context, not direct acquisition leads
        reasons.append("internal_source")

    score = min(max(score, 0), 100)
    reason = ", ".join(sorted(set(reasons))[:4]) if reasons else "low_signal"
    return score, reason


def write_shortlist(leads: list[dict[str, Any]]) -> dict[str, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_json = OUTPUT_DIR / "drafts" / f"lead_shortlist_{stamp}.json"
    out_md = OUTPUT_DIR / "drafts" / "latest_lead_shortlist.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "leads": leads}, indent=2), encoding="utf-8")

    lines = ["# SimpliXio Lead Shortlist", ""]
    if not leads:
        lines.append("- No fit or candidate leads in this run.")
    else:
        for idx, lead in enumerate(leads, start=1):
            lines.extend(
                [
                    f"## {idx}. {lead['title']}",
                    f"- Source: {lead['source']}",
                    f"- Score: {lead['fit_score']}",
                    f"- Status: {lead['status']}",
                    f"- Pain: {lead['pain_signal']}",
                    f"- URL: {lead['source_url']}",
                    "",
                ]
            )
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(out_json), "markdown": str(out_md)}


def run() -> dict[str, Any]:
    threshold = load_threshold()
    candidate_gap = load_candidate_gap()
    candidate_threshold = max(0, threshold - candidate_gap)
    conn = connect()
    init_db(conn)

    leads = list_leads_for_scoring(conn, limit=300)
    fit = 0
    candidate = 0
    not_fit = 0
    shortlist: list[dict[str, Any]] = []

    for lead in leads:
        score, reason = score_lead(lead.title, lead.source, lead.raw_payload)
        if score >= threshold:
            status = "fit"
            next_action = "draft_outreach"
        elif score >= candidate_threshold:
            status = "candidate"
            next_action = "manual_review"
        else:
            status = "not_fit"
            next_action = "archive"
        update_lead_score(
            conn,
            lead_id=lead.id,
            fit_score=score,
            pain_signal=lead.pain_signal or reason,
            status=status,
            next_action=next_action,
        )
        if status == "fit":
            fit += 1
            shortlist.append(
                {
                    "source": lead.source,
                    "title": lead.title,
                    "source_url": lead.source_url,
                    "fit_score": score,
                    "status": status,
                    "fit_level": "high",
                    "pain_signal": lead.pain_signal or reason,
                }
            )
        elif status == "candidate":
            candidate += 1
            shortlist.append(
                {
                    "source": lead.source,
                    "title": lead.title,
                    "source_url": lead.source_url,
                    "fit_score": score,
                    "status": status,
                    "fit_level": "medium",
                    "pain_signal": lead.pain_signal or reason,
                }
            )
        else:
            not_fit += 1

    shortlist = sorted(shortlist, key=lambda x: int(x["fit_score"]), reverse=True)[:20]
    shortlist_paths = write_shortlist(shortlist)

    return {
        "status": "ok",
        "threshold": threshold,
        "candidate_threshold": candidate_threshold,
        "scored": len(leads),
        "fit": fit,
        "candidate": candidate,
        "not_fit": not_fit,
        "fit_levels": {
            "high": fit,
            "medium": candidate,
            "low_or_not_fit": not_fit,
        },
        "shortlist_count": len(shortlist),
        "shortlist": shortlist_paths,
    }


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
