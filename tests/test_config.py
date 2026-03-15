"""Unit tests for the CortexOS configuration system."""

from cortex_core.config import CortexConfig, LLMConfig


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig()
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.4
        assert cfg.max_tokens == 2048

    def test_resolve_api_key_from_field(self):
        cfg = LLMConfig(api_key="sk-test")
        assert cfg.resolve_api_key() == "sk-test"

    def test_resolve_api_key_empty(self):
        cfg = LLMConfig(api_key="")
        # Falls back to env var
        key = cfg.resolve_api_key()
        # Just check it doesn't crash and returns a string
        assert isinstance(key, str)


class TestCortexConfig:
    def test_defaults(self):
        cfg = CortexConfig()
        assert cfg.api_port == 8420
        assert cfg.api_host == "0.0.0.0"
        assert cfg.knowledge_file == "knowledge_notes.json"

    def test_knowledge_path(self, tmp_data_dir):
        cfg = CortexConfig(data_dir=tmp_data_dir)
        assert cfg.knowledge_path == tmp_data_dir / "knowledge_notes.json"

    def test_posts_path(self, tmp_data_dir):
        cfg = CortexConfig(data_dir=tmp_data_dir)
        assert cfg.posts_path == tmp_data_dir / "posts_today.txt"

    def test_save_and_load(self, tmp_data_dir):
        cfg = CortexConfig(data_dir=tmp_data_dir, api_port=9999)
        cfg.save()
        cfg_path = tmp_data_dir / "config.json"
        assert cfg_path.exists()

        loaded = CortexConfig.load(cfg_path)
        assert loaded.api_port == 9999

    def test_load_nonexistent_returns_defaults(self, tmp_data_dir):
        cfg = CortexConfig.load(tmp_data_dir / "nonexistent.json")
        assert cfg.api_port == 8420

    def test_llm_config_roundtrip(self, tmp_data_dir):
        cfg = CortexConfig(data_dir=tmp_data_dir)
        cfg.llm = LLMConfig(provider="anthropic", model="claude-3.5-sonnet")
        cfg.save()

        loaded = CortexConfig.load(tmp_data_dir / "config.json")
        assert loaded.llm.provider == "anthropic"
        assert loaded.llm.model == "claude-3.5-sonnet"
