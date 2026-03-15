"""
Scoring Engine
---------------
Scores articles and knowledge items by AI relevance, signal
strength, context overlap, and project fit. This is the core
intelligence that separates CortexOS from a dumb news feed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Keyword dictionaries ───────────────────────────────────────

AI_KEYWORDS: set[str] = {
    "ai",
    "artificial",
    "intelligence",
    "model",
    "models",
    "llm",
    "llms",
    "agent",
    "agents",
    "context",
    "prompt",
    "prompts",
    "embedding",
    "embeddings",
    "inference",
    "training",
    "reasoning",
    "vision",
    "nlp",
    "robotics",
    "rag",
    "retrieval",
    "transformer",
    "diffusion",
    "gpt",
    "claude",
    "gemini",
    "anthropic",
    "openai",
    "deepmind",
    "meta ai",
    "fine-tuning",
    "fine tuning",
    "finetuning",
    "vector",
    "orchestration",
    "hallucination",
    "grounding",
    "evaluation",
    "benchmark",
}

HIGH_SIGNAL_KEYWORDS: set[str] = {
    "ai",
    "agent",
    "agents",
    "context",
    "model",
    "models",
    "reasoning",
    "robotics",
    "developer",
    "infrastructure",
    "evaluation",
    "security",
    "ethics",
    "governance",
    "productivity",
    "retrieval",
    "knowledge",
    "learning",
    "architecture",
    "pipeline",
    "observability",
    "system",
    "framework",
    "tool",
    "workflow",
    "automation",
}

NOISE_KEYWORDS: set[str] = {
    "spotify",
    "spielberg",
    "facebook",
    "headphone",
    "headphones",
    "digg",
    "celebrity",
    "gossip",
    "tiktok",
    "instagram",
    "dating",
    "reality tv",
    "kardashian",
}

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")
ARTICLE_PATTERN = re.compile(r"^- \[(.*?)\]\((.*?)\)", re.MULTILINE)


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def contains_keyword(text: str, keywords: set[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


# ── Per-article scoring ────────────────────────────────────────


@dataclass
class ArticleScore:
    """Score for a single article."""

    title: str
    url: str = ""
    ai_related: float = 0.0
    high_signal: float = 0.0
    context_overlap: float = 0.0
    noise: float = 0.0
    composite: float = 0.0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "ai_related": self.ai_related,
            "high_signal": self.high_signal,
            "context_overlap": self.context_overlap,
            "noise": self.noise,
            "composite": round(self.composite, 3),
        }


def score_article(title: str, url: str, context_tokens: set[str]) -> ArticleScore:
    """Score a single article against keywords and user context."""
    title_lower = title.lower()
    title_tokens = set(tokenize(title_lower))

    ai = 1.0 if contains_keyword(title_lower, AI_KEYWORDS) else 0.0
    signal = 1.0 if contains_keyword(title_lower, HIGH_SIGNAL_KEYWORDS) else 0.0
    noise = 1.0 if contains_keyword(title_lower, NOISE_KEYWORDS) else 0.0

    overlap = len(title_tokens & context_tokens) / max(len(title_tokens), 1)

    # Weighted composite: signal and AI relevance dominate
    composite = 0.35 * ai + 0.30 * signal + 0.25 * overlap - 0.10 * noise

    return ArticleScore(
        title=title,
        url=url,
        ai_related=ai,
        high_signal=signal,
        context_overlap=round(overlap, 3),
        noise=noise,
        composite=max(0.0, composite),
    )


# ── Digest-level evaluation ────────────────────────────────────


@dataclass
class DigestScore:
    """Aggregate metrics for a full digest."""

    total_articles: int = 0
    ai_article_ratio: float = 0.0
    high_signal_ratio: float = 0.0
    signal_to_noise_ratio: float = 0.0
    context_keyword_coverage: float = 0.0
    project_fit_score: float = 0.0
    articles: list[ArticleScore] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_articles": self.total_articles,
            "ai_article_ratio": round(self.ai_article_ratio, 3),
            "high_signal_ratio": round(self.high_signal_ratio, 3),
            "signal_to_noise_ratio": round(self.signal_to_noise_ratio, 3),
            "context_keyword_coverage": round(self.context_keyword_coverage, 3),
            "project_fit_score": round(self.project_fit_score, 3),
            "articles": [a.to_dict() for a in self.articles],
        }


def evaluate_digest(
    markdown_text: str,
    context_snippets: list[str],
) -> DigestScore:
    """Score an entire digest markdown file."""
    matches = ARTICLE_PATTERN.findall(markdown_text)

    if not matches:
        return DigestScore()

    # Build context token set from user context snippets
    context_tokens: set[str] = set()
    for snippet in context_snippets:
        context_tokens.update(tokenize(snippet))

    scores = [score_article(title, url, context_tokens) for title, url in matches]

    total = len(scores)
    ai_count = sum(1 for s in scores if s.ai_related > 0)
    signal_count = sum(1 for s in scores if s.high_signal > 0)
    noise_count = sum(1 for s in scores if s.noise > 0)

    # Digest-level keyword coverage
    digest_tokens: set[str] = set()
    for title, _ in matches:
        digest_tokens.update(tokenize(title))
    matched_context = context_tokens & digest_tokens
    coverage = len(matched_context) / max(len(context_tokens), 1)

    ai_ratio = ai_count / total
    signal_ratio = signal_count / total
    sn_ratio = signal_count / max(noise_count, 1)

    fit = 0.40 * ai_ratio + 0.35 * signal_ratio + 0.15 * min(sn_ratio / 3, 1.0) + 0.10 * coverage

    return DigestScore(
        total_articles=total,
        ai_article_ratio=ai_ratio,
        high_signal_ratio=signal_ratio,
        signal_to_noise_ratio=sn_ratio,
        context_keyword_coverage=coverage,
        project_fit_score=fit,
        articles=sorted(scores, key=lambda s: s.composite, reverse=True),
    )


def filter_high_signal(digest_score: DigestScore, threshold: float = 0.3) -> list[ArticleScore]:
    """Return only articles above the composite threshold."""
    return [a for a in digest_score.articles if a.composite >= threshold]
