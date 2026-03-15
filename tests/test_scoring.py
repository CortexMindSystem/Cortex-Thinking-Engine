"""Unit tests for the scoring engine."""

from cortex_core.scoring import (
    DigestScore,
    contains_keyword,
    evaluate_digest,
    filter_high_signal,
    score_article,
    tokenize,
)


class TestTokenize:
    def test_basic_words(self):
        assert tokenize("Hello World") == ["hello", "world"]

    def test_strips_punctuation(self):
        tokens = tokenize("AI-powered, context-engine!")
        assert "ai" in tokens
        assert "powered" in tokens
        assert "context" in tokens

    def test_empty_string(self):
        assert tokenize("") == []

    def test_numbers_included(self):
        tokens = tokenize("GPT4 model v2")
        assert "gpt4" in tokens
        assert "v2" in tokens


class TestContainsKeyword:
    def test_single_match(self):
        assert contains_keyword("New AI model released", {"ai", "llm"})

    def test_no_match(self):
        assert not contains_keyword("Spotify playlist update", {"ai", "llm"})

    def test_case_insensitive(self):
        assert contains_keyword("New LLM Benchmark", {"llm"})

    def test_multi_word_keyword(self):
        assert contains_keyword("Latest from Meta AI labs", {"meta ai"})


class TestScoreArticle:
    def test_ai_article_scores_high(self):
        score = score_article(
            "OpenAI launches new AI agent framework",
            "https://openai.com/agent",
            {"ai", "agent", "context", "retrieval"},
        )
        assert score.ai_related == 1.0
        assert score.high_signal == 1.0
        assert score.composite > 0.5

    def test_noise_article_scores_low(self):
        score = score_article(
            "Spotify lets you edit your Taste Profile",
            "https://spotify.com",
            {"ai", "context"},
        )
        assert score.noise == 1.0
        assert score.composite < 0.3

    def test_neutral_article(self):
        score = score_article(
            "Quarterly earnings report published",
            "https://example.com",
            {"ai"},
        )
        assert score.ai_related == 0.0
        assert score.high_signal == 0.0
        assert score.noise == 0.0

    def test_composite_never_negative(self):
        score = score_article("Spotify celebrity gossip", "url", set())
        assert score.composite >= 0.0

    def test_context_overlap(self):
        score = score_article(
            "New retrieval benchmark for AI agents",
            "url",
            {"retrieval", "benchmark", "agents", "ai"},
        )
        assert score.context_overlap > 0


class TestEvaluateDigest:
    def test_returns_digest_score(self, sample_digest_text, sample_context_snippets):
        result = evaluate_digest(sample_digest_text, sample_context_snippets)
        assert isinstance(result, DigestScore)
        assert result.total_articles > 0

    def test_ai_ratio_above_zero(self, sample_digest_text, sample_context_snippets):
        result = evaluate_digest(sample_digest_text, sample_context_snippets)
        assert result.ai_article_ratio > 0

    def test_high_signal_ratio_above_zero(self, sample_digest_text, sample_context_snippets):
        result = evaluate_digest(sample_digest_text, sample_context_snippets)
        assert result.high_signal_ratio > 0

    def test_project_fit_score_bounded(self, sample_digest_text, sample_context_snippets):
        result = evaluate_digest(sample_digest_text, sample_context_snippets)
        assert 0 <= result.project_fit_score <= 1.0

    def test_articles_sorted_by_composite(self, sample_digest_text, sample_context_snippets):
        result = evaluate_digest(sample_digest_text, sample_context_snippets)
        composites = [a.composite for a in result.articles]
        assert composites == sorted(composites, reverse=True)

    def test_empty_digest(self, sample_context_snippets):
        result = evaluate_digest("No articles here", sample_context_snippets)
        assert result.total_articles == 0

    def test_empty_context(self, sample_digest_text):
        result = evaluate_digest(sample_digest_text, [])
        assert isinstance(result, DigestScore)
        assert result.total_articles > 0

    def test_to_dict(self, sample_digest_text, sample_context_snippets):
        result = evaluate_digest(sample_digest_text, sample_context_snippets)
        d = result.to_dict()
        assert "total_articles" in d
        assert "ai_article_ratio" in d
        assert "articles" in d


class TestFilterHighSignal:
    def test_filters_low_scores(self, sample_digest_text, sample_context_snippets):
        result = evaluate_digest(sample_digest_text, sample_context_snippets)
        filtered = filter_high_signal(result, threshold=0.3)
        for article in filtered:
            assert article.composite >= 0.3

    def test_empty_digest(self):
        empty = DigestScore()
        assert filter_high_signal(empty, threshold=0.5) == []
