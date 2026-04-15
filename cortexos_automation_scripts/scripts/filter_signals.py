#!/usr/bin/env python3
"""Filter digest signals into core / adjacent / ignore buckets.

Monorepo-aware:
- reads digest files from repo root (default: weekly_digest_*.md)
- writes filtered outputs into cortexos_automation_scripts/output/filtered_signals
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTOMATION_ROOT.parent

RAW_DIGEST_GLOB = os.getenv("DIGEST_GLOB", "weekly_digest_*.md")
OUTPUT_DIR = AUTOMATION_ROOT / "output" / "filtered_signals"

CORE_KEYWORDS = {
    "context",
    "memory",
    "agent",
    "agents",
    "reasoning",
    "decision",
    "decisions",
    "workflow",
    "workflows",
    "retrieval",
    "rag",
    "signal",
    "priority",
    "priorities",
    "knowledge",
    "evaluation",
    "developer",
    "builders",
    "automation",
    "orchestration",
    "long context",
    "inference",
}

ADJACENT_KEYWORDS = {
    "robotics",
    "chips",
    "security",
    "privacy",
    "local ai",
    "open source",
    "productivity",
    "calendar",
    "search",
    "analytics",
    "integration",
    "github",
    "notion",
}

IGNORE_KEYWORDS = {
    "celebrity",
    "film",
    "spotify",
    "facebook",
    "impersonator",
    "headphones",
    "digg",
    "gaming",
    "movie",
    "music",
}

ARTICLE_PATTERN = re.compile(r"^- \[(.*?)\]\((.*?)\)", re.MULTILINE)


@dataclass
class SignalItem:
    title: str
    url: str
    category: str
    score: float
    reasons: list[str]


def normalize(text: str) -> str:
    return text.lower().strip()


def contains_phrase(text: str, phrases: set[str]) -> list[str]:
    text_lower = normalize(text)
    return [phrase for phrase in phrases if phrase in text_lower]


def extract_articles(markdown_text: str) -> list[tuple[str, str]]:
    return ARTICLE_PATTERN.findall(markdown_text)


def score_signal(title: str, url: str) -> SignalItem:
    text = normalize(title)

    core_hits = contains_phrase(text, CORE_KEYWORDS)
    adjacent_hits = contains_phrase(text, ADJACENT_KEYWORDS)
    ignore_hits = contains_phrase(text, IGNORE_KEYWORDS)

    score = 0.0
    reasons: list[str] = []

    if core_hits:
        score += 2.0 * len(core_hits)
        reasons.extend([f"core:{hit}" for hit in core_hits])
    if adjacent_hits:
        score += 0.75 * len(adjacent_hits)
        reasons.extend([f"adjacent:{hit}" for hit in adjacent_hits])
    if ignore_hits:
        score -= 2.5 * len(ignore_hits)
        reasons.extend([f"ignore:{hit}" for hit in ignore_hits])

    if "ai" in text:
        score += 0.5
        reasons.append("core:ai")
    if "context" in text or "memory" in text:
        score += 1.5

    if score >= 2.5:
        category = "core"
    elif score >= 0.5:
        category = "adjacent"
    else:
        category = "ignore"

    return SignalItem(
        title=title.strip(),
        url=url.strip(),
        category=category,
        score=round(score, 2),
        reasons=reasons,
    )


def latest_digest_file() -> Path:
    files = sorted(REPO_ROOT.glob(RAW_DIGEST_GLOB))
    if not files:
        raise FileNotFoundError(
            f"No digest file found in {REPO_ROOT} matching '{RAW_DIGEST_GLOB}'."
        )
    return files[-1]


def build_outputs(items: list[SignalItem], digest_file: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[dict]] = {"core": [], "adjacent": [], "ignore": []}
    for item in items:
        grouped[item.category].append(asdict(item))

    json_path = OUTPUT_DIR / f"{digest_file.stem}_filtered.json"
    json_path.write_text(json.dumps(grouped, indent=2), encoding="utf-8")

    lines: list[str] = [f"# Filtered Signals for {digest_file.stem}", ""]
    for bucket in ("core", "adjacent", "ignore"):
        lines.append(f"## {bucket.title()}")
        if not grouped[bucket]:
            lines.append("- None")
        else:
            for item in grouped[bucket]:
                reasons = ", ".join(item["reasons"]) if item["reasons"] else "none"
                lines.append(
                    f"- [{item['title']}]({item['url']})  \n"
                    f"  score: {item['score']}  \n"
                    f"  reasons: {reasons}"
                )
        lines.append("")

    md_path = OUTPUT_DIR / f"{digest_file.stem}_filtered.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    digest_file = latest_digest_file()
    markdown_text = digest_file.read_text(encoding="utf-8")
    articles = extract_articles(markdown_text)

    items = [score_signal(title, url) for title, url in articles]
    build_outputs(items, digest_file)

    counts = Counter(item.category for item in items)
    print(
        json.dumps(
            {
                "file": str(digest_file),
                "total": len(items),
                "counts": dict(counts),
                "output_dir": str(OUTPUT_DIR),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
