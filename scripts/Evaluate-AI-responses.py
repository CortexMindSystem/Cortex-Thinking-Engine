#!/usr/bin/env python3
"""
AI Response / Digest Evaluator
-------------------------------
Evaluates the quality and relevance of a weekly digest against
the user's CortexOS context. Uses the scoring engine for proper
metrics instead of naive word overlap.

Usage:
    python3 scripts/Evaluate-AI-responses.py
"""

import json
import sys
from pathlib import Path

# Add project root to path so imports work from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cortex_core.scoring import evaluate_digest


def find_latest_digest() -> Path:
    """Find the most recent weekly digest file."""
    # Check current directory first, then project root
    for search_dir in [Path("."), Path(__file__).resolve().parent.parent]:
        files = sorted(search_dir.glob("weekly_digest_*.md"))
        if files:
            return files[-1]
    raise FileNotFoundError("No weekly_digest_*.md file found.")


if __name__ == "__main__":
    # Default context aligned with CortexOS project thesis
    context = [
        "The weekly digest covers the latest advancements in AI including models and applications.",
        "This week we saw significant improvements in natural language processing and computer vision.",
        "Several companies announced partnerships to integrate AI into their products.",
        "Ethical considerations in AI development continue to be a major focus for researchers and policymakers.",
        "The digest also highlights upcoming AI conferences and events in the next month.",
        "AI agents and context-aware systems are the core focus of CortexOS.",
        "Developer productivity tools and knowledge management systems are key interests.",
        "Retrieval augmented generation and evaluation frameworks matter for the project.",
    ]

    digest_file = find_latest_digest()

    with open(digest_file, encoding="utf-8") as f:
        digest_content = f.read()

    score = evaluate_digest(digest_content, context)

    output = {
        "file": str(digest_file),
        "metrics": {
            "total_articles": score.total_articles,
            "ai_article_ratio": score.ai_article_ratio,
            "high_signal_ratio": score.high_signal_ratio,
            "signal_to_noise_ratio": score.signal_to_noise_ratio,
            "context_keyword_coverage": score.context_keyword_coverage,
            "project_fit_score": score.project_fit_score,
        },
        "top_articles": [{"title": a.title, "score": a.composite} for a in score.articles[:5]],
    }

    print(json.dumps(output, indent=2))
