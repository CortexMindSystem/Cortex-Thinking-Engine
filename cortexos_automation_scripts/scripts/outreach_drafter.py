#!/usr/bin/env python3
"""Draft private outreach messages for approval.

Never sends. All drafts default to needs_approval.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from acquisition_crm import (
    OUTPUT_DIR,
    connect,
    init_db,
    insert_message,
    list_fit_leads_for_outreach,
    recent_message_hashes,
    text_hash,
)


def build_private_draft(lead_title: str, lead_url: str, pain_signal: str) -> str:
    reason = pain_signal if pain_signal and pain_signal != "Unknown" else "signal vs noise overload"
    return (
        "Hi,\n\n"
        f"I noticed your recent work: {lead_title} ({lead_url}).\n"
        f"The signal I picked up is {reason}.\n\n"
        "I am building SimpliXio, a decision system that turns noise into 3 priorities:\n"
        "- what matters\n"
        "- why it matters\n"
        "- what to do next\n\n"
        "If helpful, I can share a short demo with real daily outputs (including ignored signals).\n\n"
        "No pressure. I thought this might be relevant to what you are building."
    )


def run(limit: int = 30) -> dict[str, Any]:
    conn = connect()
    init_db(conn)
    leads = list_fit_leads_for_outreach(conn, limit=limit)
    prior_hashes = recent_message_hashes(conn, limit=120)

    created = 0
    skipped_repeated = 0
    from_fit = 0
    from_candidate = 0
    drafts: list[dict[str, Any]] = []

    for lead in leads:
        draft = build_private_draft(lead.title, lead.source_url, lead.pain_signal)
        hash_value = text_hash(draft)
        if hash_value in prior_hashes:
            skipped_repeated += 1
            continue

        message_id = insert_message(
            conn,
            lead_id=lead.id,
            channel="private_outreach",
            message_type="private",
            draft_text=draft,
            status="needs_approval",
            compliance_notes="Private outbound requires explicit manual approval.",
        )
        created += 1
        if lead.status == "fit":
            from_fit += 1
        drafts.append(
            {
                "message_id": message_id,
                "lead_id": lead.id,
                "fit_score": lead.fit_score,
                "lead_status": lead.status,
                "title": lead.title,
                "source_url": lead.source_url,
                "draft": draft,
            }
        )
        prior_hashes.add(hash_value)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUTPUT_DIR / "drafts" / f"outreach_{stamp}.json"
    out_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "created": created,
                "skipped_repeated": skipped_repeated,
                "from_fit": from_fit,
                "from_candidate": from_candidate,
                "drafts": drafts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    md_path = OUTPUT_DIR / "drafts" / "latest_outreach.md"
    lines = ["# SimpliXio Outreach Drafts", ""]
    if not drafts:
        lines.append("- No new drafts generated.")
    else:
        for item in drafts:
            lines.extend(
                [
                    f"## Lead {item['lead_id']} · fit {item['fit_score']}",
                    f"- Title: {item['title']}",
                    f"- URL: {item['source_url']}",
                    f"- Message ID: {item['message_id']}",
                    "",
                    item["draft"],
                    "",
                    "---",
                    "",
                ]
            )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "status": "ok",
        "created": created,
        "skipped_repeated": skipped_repeated,
        "from_fit": from_fit,
        "from_candidate": 0,
        "json": str(out_path),
        "markdown": str(md_path),
    }


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
