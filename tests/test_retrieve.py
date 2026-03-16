"""Tests for Hybrid Retrieval."""

import pytest
from datetime import datetime

from cortex_core.retrieve import HybridRetriever, RetrievalResult
from cortex_core.items import Item


class TestRetrievalResult:
    def test_create_result(self):
        r = RetrievalResult(id="1", title="Test", content="hello", score=0.8, match_reasons=["keyword"])
        assert r.score == 0.8
        assert "keyword" in r.match_reasons

    def test_to_dict(self):
        r = RetrievalResult(id="1", title="Test", content="hello", score=0.5, match_reasons=["tag"])
        d = r.to_dict()
        assert d["id"] == "1"
        assert d["score"] == 0.5


class TestHybridRetriever:
    @pytest.fixture()
    def items(self):
        now = datetime.now().isoformat()
        return [
            Item(
                source_type="newsletter",
                title="AI Agent Framework Released",
                content="A new framework for building AI agents launched today.",
                tags=["ai", "agents", "framework"],
                ingested_at=now,
            ),
            Item(
                source_type="newsletter",
                title="Context Engineering Guide",
                content="How to build better context for LLM applications.",
                tags=["context", "llm"],
                ingested_at=now,
            ),
            Item(
                source_type="paper",
                title="Memory Systems in AI",
                content="Survey of memory architectures for intelligent agents.",
                tags=["memory", "ai", "research"],
                ingested_at=now,
            ),
            Item(
                source_type="tweet",
                title="Quick tip on Python async",
                content="Use asyncio.gather for parallel tasks.",
                tags=["python", "async"],
                ingested_at=now,
            ),
        ]

    @pytest.fixture()
    def retriever(self, items):
        return HybridRetriever(items=items)

    def test_keyword_search(self, retriever):
        results = retriever.retrieve(query="ai agents")
        assert len(results) >= 1
        titles = [r.title for r in results]
        assert "AI Agent Framework Released" in titles

    def test_tag_filter(self, retriever):
        results = retriever.retrieve(query="", tags=["memory"])
        assert len(results) >= 1
        titles = [r.title for r in results]
        assert "Memory Systems in AI" in titles

    def test_source_type_filter(self, retriever):
        results = retriever.retrieve(query="", source_type="paper")
        assert len(results) >= 1
        assert all(r.title == "Memory Systems in AI" for r in results)

    def test_combined_filters(self, retriever):
        results = retriever.retrieve(query="framework", tags=["ai"])
        # Should prioritise the AI Agent Framework item
        assert len(results) >= 1
        assert results[0].title == "AI Agent Framework Released"

    def test_empty_query_returns_all_matching(self, retriever):
        results = retriever.retrieve(query="", source_type="newsletter")
        assert len(results) == 2

    def test_top_k_limit(self, retriever):
        results = retriever.retrieve(query="ai", top_k=2)
        assert len(results) <= 2

    def test_no_results(self, retriever):
        results = retriever.retrieve(query="quantum computing blockchain")
        assert len(results) == 0

    def test_title_match_bonus(self, retriever):
        results = retriever.retrieve(query="context engineering")
        if results:
            assert results[0].title == "Context Engineering Guide"

    def test_results_sorted_by_score(self, retriever):
        results = retriever.retrieve(query="ai")
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_match_reasons_populated(self, retriever):
        results = retriever.retrieve(query="ai", tags=["memory"])
        for r in results:
            assert len(r.match_reasons) >= 1
