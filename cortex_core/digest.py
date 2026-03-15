"""
Digest Processor
-----------------
Reads weekly Markdown digests, extracts articles/links,
and produces structured knowledge notes (optionally via LLM).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cortex_core.knowledge import KnowledgeNote, KnowledgeStore
from cortex_core.llm import LLMProvider

ARTICLE_PATTERN = re.compile(r"- \[(.*?)\]\((.*?)\)")
HEADING_PATTERN = re.compile(r"^#{1,3}\s+(.+)", re.MULTILINE)


@dataclass
class ExtractedArticle:
    title: str
    url: str
    section: str = ""


class DigestProcessor:
    """Parse markdown digests and turn them into knowledge notes."""

    def __init__(
        self,
        store: KnowledgeStore,
        llm: LLMProvider | None = None,
    ):
        self.store = store
        self.llm = llm

    # --------------------------------------------------------- extraction

    @staticmethod
    def extract_articles(text: str) -> list[ExtractedArticle]:
        """Pull all markdown links from a digest."""
        current_section = ""
        articles: list[ExtractedArticle] = []

        for line in text.splitlines():
            heading_match = HEADING_PATTERN.match(line)
            if heading_match:
                current_section = heading_match.group(1).strip()
            for title, url in ARTICLE_PATTERN.findall(line):
                articles.append(ExtractedArticle(title=title, url=url, section=current_section))
        return articles

    # --------------------------------------------------------- processing

    def process_file(self, path: Path, *, use_llm: bool = False) -> list[KnowledgeNote]:
        """Process a single digest file into knowledge notes."""
        text = path.read_text()
        articles = self.extract_articles(text)
        notes: list[KnowledgeNote] = []

        for article in articles:
            note = self._llm_summarise(article) if use_llm and self.llm else self._rule_summarise(article)
            self.store.add(note)
            notes.append(note)

        return notes

    def process_latest(self, directory: Path, *, use_llm: bool = False) -> list[KnowledgeNote]:
        """Find the most recent digest in *directory* and process it."""
        candidates = sorted(directory.glob("weekly_digest_*.md"))
        if not candidates:
            return []
        return self.process_file(candidates[-1], use_llm=use_llm)

    # ---------------------------------------------------------- strategies

    @staticmethod
    def _rule_summarise(article: ExtractedArticle) -> KnowledgeNote:
        tags = _infer_article_tags(article.title)
        if article.section and article.section not in tags:
            tags.insert(0, article.section)
        return KnowledgeNote(
            title=article.title,
            source_url=article.url,
            insight=f"{article.title} highlights a key shift in AI or technology.",
            implication="Investigate how this affects CortexOS context ranking.",
            action="Add note to research backlog.",
            tags=tags,
        )

    def _llm_summarise(self, article: ExtractedArticle) -> KnowledgeNote:
        prompt = (
            f"Summarise this article for a knowledge worker building an AI context engine.\n"
            f"Title: {article.title}\nURL: {article.url}\nSection: {article.section}\n\n"
            "Return JSON with keys: insight, implication, action, tags (list)."
        )
        resp = self.llm.generate(prompt)  # type: ignore[union-attr]
        try:
            import json

            data = json.loads(resp.text)
        except Exception:
            return self._rule_summarise(article)

        return KnowledgeNote(
            title=article.title,
            source_url=article.url,
            insight=data.get("insight", ""),
            implication=data.get("implication", ""),
            action=data.get("action", ""),
            tags=data.get("tags", ["digest"]),
        )


# ── Tag inference ──────────────────────────────────────────────

_TAG_MAP: dict[str, list[str]] = {
    "ai": ["ai", "artificial", "llm", "gpt", "claude", "gemini", "openai", "anthropic"],
    "agents": ["agent", "agents", "agentic"],
    "retrieval": ["retrieval", "rag", "context", "vector", "search", "embedding"],
    "infrastructure": ["infrastructure", "chip", "supply", "data center", "cloud"],
    "robotics": ["robot", "robotics"],
    "safety": ["safety", "ethics", "risk", "bias", "regulation", "governance"],
    "developer-tools": ["developer", "docker", "github", "tool", "sdk", "api"],
    "productivity": ["productivity", "focus", "learning", "workflow"],
    "health": ["health", "medical", "clinical", "heart", "brain"],
    "business": ["startup", "founder", "funding", "revenue", "market"],
}


def _infer_article_tags(title: str) -> list[str]:
    """Infer topic tags from an article title."""
    title_lower = title.lower()
    tags = []
    for tag, keywords in _TAG_MAP.items():
        if any(kw in title_lower for kw in keywords):
            tags.append(tag)
    return tags or ["general"]
