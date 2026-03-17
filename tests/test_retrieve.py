"""Tests for Hybrid Retrieval system."""

from datetime import datetime, timedelta

import pytest

from cortex_core.retrieve import HybridRetriever, RetrievalResult


def _make_item(title, content="", source_type="article", tags=None, days_ago=0):
    ts = (datetime.now() - timedelta(days=days_ago)).isoformat()
    return {
        "id": title.lower().replace(" ", "-"),
        "source_type": source_type,
        "title": title,
        "content": content or f"Content about {title}",
        "tags": tags or [],
        "ingested_at": ts,
    }


class TestRetrievalResult:
    def test_create_result(self):
        r = RetrievalResult(id="1", title="Test", content="body", score=0.8, match_reasons=["keyword"])
        assert r.score == 0.8
        assert "keyword" in r.match_reasons


class TestHybridRetriever:
    @pytest.fixture()
    def retriever(self):
        return HybridRetriever()

    def test_empty_retrieval(self, retriever):
        results = retriever.retrieve("anything", [])
        assert results == []

    def test_keyword_match(self, retriever):
        items = [
            _make_item("AI Agent Framework", "Guide to building AI agents"),
            _make_item("Cooking Recipes", "How to make pasta"),
        ]
        results = retriever.retrieve("AI agent", items)
        assert len(results) >= 1
        assert results[0].title == "AI Agent Framework"

    def test_title_bonus(self, retriever):
        items = [
            _make_item("Context Engineering", "Brief mention of context"),
            _make_item("Random Title", "Deep dive into context engineering patterns"),
        ]
        results = retriever.retrieve("context engineering", items)
        assert any(r.title == "Context Engineering" for r in results)

    def test_recency_boost(self, retriever):
        items = [
            _make_item("Recent Article", "AI context memory", days_ago=1),
            _make_item("Old Article", "AI context memory", days_ago=30),
        ]
        results = retriever.retrieve("AI context memory", items)
        assert len(results) >= 2
        recent = next(r for r in results if r.title == "Recent Article")
        old = next(r for r in results if r.title == "Old Article")
        assert recent.score >= old.score

    def test_source_type_filter(self, retriever):
        items = [
            _make_item("Paper A", source_type="paper", content="AI research"),
            _make_item("Article A", source_type="article", content="AI research"),
        ]
        results = retriever.retrieve("AI research", items, source_type="paper")
        assert all(r.title == "Paper A" for r in results)

    def test_tag_filter(self, retriever):
        items = [
            _make_item("Tagged A", tags=["ml"], content="machine learning stuff"),
            _make_item("Tagged B", tags=["web"], content="machine learning stuff"),
        ]
        results = retriever.retrieve("machine learning", items, tags=["ml"])
        assert len(results) >= 1
        assert results[0].title == "Tagged A"

    def test_recency_filter(self, retriever):
        items = [
            _make_item("New", content="AI tools", days_ago=3),
            _make_item("Old", content="AI tools", days_ago=60),
        ]
        results = retriever.retrieve("AI tools", items, recency_days=7)
        titles = [r.title for r in results]
        assert "New" in titles
        assert "Old" not in titles

    def test_max_results(self, retriever):
        items = [_make_item(f"AI Tool {i}", content="AI agent framework") for i in range(20)]
        results = retriever.retrieve("AI agent", items, max_results=5)
        assert len(results) <= 5

    def test_no_match(self, retriever):
        items = [_make_item("Cooking Tips", "How to bake bread")]
        results = retriever.retrieve("quantum computing", items)
        assert len(results) == 0
