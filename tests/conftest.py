"""Shared test fixtures for CortexOS unit tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Provide a temporary data directory for tests."""
    d = tmp_path / "cortexos_data"
    d.mkdir()
    return d


@pytest.fixture
def sample_digest_text():
    """A realistic digest markdown string for testing."""
    return """# Weekly AI Digest — 2026-03-14

## Recent articles
- [OpenAI launches new AI agent framework](https://openai.com/blog/agent-framework) — March 14, 2026
- [Anthropic Claude context window extended to 1M tokens](https://anthropic.com/blog/1m-context) — March 13, 2026
- [Google Gemini now integrated into Workspace](https://blog.google/gemini-workspace) — March 12, 2026
- [Travis Kalanick launches robotics company Atoms](https://techcrunch.com/atoms-robotics) — March 13, 2026
- [Spotify lets you edit your Taste Profile](https://techcrunch.com/spotify-profile) — March 13, 2026
- [Developer productivity tools see massive AI adoption](https://devtools.io/ai-adoption) — March 11, 2026
- [New vector search benchmark released](https://paperswithcode.com/vector-benchmark) — March 10, 2026
- [Ethics board raises concerns about AI agent autonomy](https://reuters.com/ai-ethics) — March 11, 2026

## Trending GitHub repositories
- **langchain-ai/langchain** (45000 stars) — https://github.com/langchain-ai/langchain
"""


@pytest.fixture
def sample_context_snippets():
    """Context snippets representing a typical CortexOS user profile."""
    return [
        "Build CortexOS context engine",
        "Improve AI systems design skills",
        "AI agents",
        "context memory",
        "retrieval",
        "evaluation",
        "developer productivity",
        "CortexOS",
    ]


@pytest.fixture
def sample_profile_dict():
    """A serialised user profile."""
    return {
        "name": "TestBuilder",
        "goals": ["Build AI products", "Ship weekly"],
        "interests": ["AI agents", "retrieval", "evaluation"],
        "current_projects": ["CortexOS"],
        "constraints": ["Low code debt"],
        "ignored_topics": ["celebrity news"],
    }
