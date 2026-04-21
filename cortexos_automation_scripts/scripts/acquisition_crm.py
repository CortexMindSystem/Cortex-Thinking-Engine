#!/usr/bin/env python3
"""SQLite-backed acquisition CRM for SimpliXio.

Tables:
- leads
- messages
- content
- runs
- approvals
- replies
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = AUTOMATION_ROOT / "output" / "acquisition"
DB_PATH = OUTPUT_DIR / "acquisition.sqlite3"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "logs").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "summaries").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "drafts").mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_url TEXT NOT NULL,
            title TEXT NOT NULL,
            author_handle TEXT,
            pain_signal TEXT,
            fit_score INTEGER,
            status TEXT NOT NULL DEFAULT 'new',
            next_action TEXT NOT NULL DEFAULT 'score',
            raw_payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(source_url)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            channel TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'private',
            draft_text TEXT NOT NULL,
            draft_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'needs_approval',
            compliance_notes TEXT NOT NULL DEFAULT '',
            quality_score INTEGER,
            created_at TEXT NOT NULL,
            approved_at TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        );

        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            angle TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            body_hash TEXT NOT NULL,
            source_artifact TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            quality_score INTEGER,
            compliance_notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline TEXT NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            summary_json TEXT NOT NULL,
            summary_path TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT NOT NULL, -- message|content
            target_id INTEGER NOT NULL,
            approved_by TEXT NOT NULL,
            approval_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            body TEXT NOT NULL,
            sentiment TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        );

        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
        CREATE INDEX IF NOT EXISTS idx_content_status ON content(status);
        """
    )
    conn.commit()


def upsert_lead(
    conn: sqlite3.Connection,
    *,
    source: str,
    source_url: str,
    title: str,
    author_handle: str = "",
    pain_signal: str = "",
    raw_payload: dict[str, Any] | None = None,
) -> int:
    now = utc_now()
    payload = json.dumps(raw_payload or {}, ensure_ascii=False)

    conn.execute(
        """
        INSERT INTO leads (
            source, source_url, title, author_handle, pain_signal,
            raw_payload, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_url) DO UPDATE SET
            source=excluded.source,
            title=excluded.title,
            author_handle=excluded.author_handle,
            pain_signal=CASE
                WHEN leads.pain_signal IS NULL OR leads.pain_signal = '' THEN excluded.pain_signal
                ELSE leads.pain_signal
            END,
            fit_score=CASE
                WHEN leads.title != excluded.title OR leads.raw_payload != excluded.raw_payload THEN NULL
                ELSE leads.fit_score
            END,
            status=CASE
                WHEN leads.title != excluded.title OR leads.raw_payload != excluded.raw_payload THEN 'new'
                ELSE leads.status
            END,
            next_action=CASE
                WHEN leads.title != excluded.title OR leads.raw_payload != excluded.raw_payload THEN 'score'
                ELSE leads.next_action
            END,
            raw_payload=excluded.raw_payload,
            updated_at=excluded.updated_at
        """,
        (
            source.strip(),
            source_url.strip(),
            title.strip(),
            author_handle.strip(),
            pain_signal.strip(),
            payload,
            now,
            now,
        ),
    )
    conn.commit()

    row = conn.execute(
        "SELECT id FROM leads WHERE source_url = ?",
        (source_url.strip(),),
    ).fetchone()
    return int(row["id"])


def update_lead_score(
    conn: sqlite3.Connection,
    *,
    lead_id: int,
    fit_score: int,
    pain_signal: str,
    status: str,
    next_action: str,
) -> None:
    conn.execute(
        """
        UPDATE leads
        SET fit_score = ?, pain_signal = ?, status = ?, next_action = ?, updated_at = ?
        WHERE id = ?
        """,
        (fit_score, pain_signal.strip(), status, next_action, utc_now(), lead_id),
    )
    conn.commit()


def insert_message(
    conn: sqlite3.Connection,
    *,
    lead_id: int,
    channel: str,
    message_type: str,
    draft_text: str,
    status: str = "needs_approval",
    compliance_notes: str = "",
) -> int:
    draft_hash = text_hash(draft_text)
    now = utc_now()
    conn.execute(
        """
        INSERT INTO messages (
            lead_id, channel, message_type, draft_text, draft_hash,
            status, compliance_notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            channel,
            message_type,
            draft_text,
            draft_hash,
            status,
            compliance_notes,
            now,
        ),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def update_message_quality(
    conn: sqlite3.Connection,
    *,
    message_id: int,
    quality_score: int,
    status: str,
    compliance_notes: str,
) -> None:
    conn.execute(
        """
        UPDATE messages
        SET quality_score = ?, status = ?, compliance_notes = ?
        WHERE id = ?
        """,
        (quality_score, status, compliance_notes, message_id),
    )
    conn.commit()


def insert_content(
    conn: sqlite3.Connection,
    *,
    channel: str,
    angle: str,
    title: str,
    body: str,
    source_artifact: str,
    status: str = "draft",
) -> int:
    conn.execute(
        """
        INSERT INTO content (
            channel, angle, title, body, body_hash, source_artifact, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            channel,
            angle,
            title,
            body,
            text_hash(body),
            source_artifact,
            status,
            utc_now(),
        ),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def update_content_quality(
    conn: sqlite3.Connection,
    *,
    content_id: int,
    quality_score: int,
    status: str,
    compliance_notes: str,
) -> None:
    conn.execute(
        """
        UPDATE content
        SET quality_score = ?, status = ?, compliance_notes = ?
        WHERE id = ?
        """,
        (quality_score, status, compliance_notes, content_id),
    )
    conn.commit()


def insert_run(
    conn: sqlite3.Connection,
    *,
    pipeline: str,
    mode: str,
    status: str,
    summary_json: dict[str, Any],
    summary_path: str = "",
) -> int:
    conn.execute(
        """
        INSERT INTO runs (pipeline, mode, status, summary_json, summary_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            pipeline,
            mode,
            status,
            json.dumps(summary_json, ensure_ascii=False),
            summary_path,
            utc_now(),
        ),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def recent_content_hashes(conn: sqlite3.Connection, limit: int = 30) -> set[str]:
    rows = conn.execute(
        "SELECT body_hash FROM content ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {str(row["body_hash"]) for row in rows if row["body_hash"]}


def recent_message_hashes(conn: sqlite3.Connection, limit: int = 60) -> set[str]:
    rows = conn.execute(
        "SELECT draft_hash FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {str(row["draft_hash"]) for row in rows if row["draft_hash"]}


def record_approval(
    conn: sqlite3.Connection,
    *,
    target_type: str,
    target_id: int,
    approved_by: str,
    approval_note: str = "",
) -> int:
    conn.execute(
        """
        INSERT INTO approvals (target_type, target_id, approved_by, approval_note, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (target_type, target_id, approved_by.strip(), approval_note.strip(), utc_now()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


@dataclass
class Lead:
    id: int
    source: str
    source_url: str
    title: str
    author_handle: str
    pain_signal: str
    fit_score: int | None
    status: str
    next_action: str
    raw_payload: dict[str, Any]


def list_leads_for_scoring(conn: sqlite3.Connection, limit: int = 200) -> list[Lead]:
    rows = conn.execute(
        """
        SELECT * FROM leads
        WHERE status != 'do_not_contact'
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_lead_from_row(row) for row in rows]


def list_fit_leads_for_outreach(conn: sqlite3.Connection, limit: int = 30) -> list[Lead]:
    rows = conn.execute(
        """
        SELECT * FROM leads
        WHERE status = 'fit'
        ORDER BY fit_score DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_lead_from_row(row) for row in rows]


def list_best_fit_leads(conn: sqlite3.Connection, limit: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, source, source_url, title, fit_score, pain_signal, next_action
        FROM leads
        WHERE status IN ('fit', 'candidate')
        ORDER BY
            CASE status
                WHEN 'fit' THEN 0
                WHEN 'candidate' THEN 1
                ELSE 2
            END,
            fit_score DESC,
            id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_prospect_leads_for_outreach(conn: sqlite3.Connection, limit: int = 40) -> list[Lead]:
    rows = conn.execute(
        """
        SELECT * FROM leads
        WHERE status IN ('fit', 'candidate')
        ORDER BY fit_score DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_lead_from_row(row) for row in rows]


def _lead_from_row(row: sqlite3.Row) -> Lead:
    payload = {}
    try:
        payload = json.loads(str(row["raw_payload"] or "{}"))
    except Exception:
        payload = {}
    return Lead(
        id=int(row["id"]),
        source=str(row["source"]),
        source_url=str(row["source_url"]),
        title=str(row["title"]),
        author_handle=str(row["author_handle"] or ""),
        pain_signal=str(row["pain_signal"] or ""),
        fit_score=int(row["fit_score"]) if row["fit_score"] is not None else None,
        status=str(row["status"]),
        next_action=str(row["next_action"]),
        raw_payload=payload,
    )
