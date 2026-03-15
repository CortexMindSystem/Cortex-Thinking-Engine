"""
CortexOS Configuration
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".cortexos"
DEFAULT_PORT = 8420


@dataclass
class LLMConfig:
    """Settings for the LLM backend."""

    provider: str = "openai"  # openai | anthropic | local
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str | None = None
    temperature: float = 0.4
    max_tokens: int = 2048

    def resolve_api_key(self) -> str:
        """Return the key from field or environment."""
        if self.api_key:
            return self.api_key
        env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = env_map.get(self.provider, "CORTEX_LLM_API_KEY")
        return os.environ.get(env_var, "")


@dataclass
class CortexConfig:
    """Top-level runtime configuration for CortexOS."""

    data_dir: Path = DEFAULT_DATA_DIR
    knowledge_file: str = "knowledge_notes.json"
    digest_glob: str = "weekly_digest_*.md"
    posts_file: str = "posts_today.txt"
    coupons_file: str = "coupons.txt"
    api_host: str = "0.0.0.0"  # noqa: S104  # nosec B104
    api_port: int = DEFAULT_PORT
    llm: LLMConfig = field(default_factory=LLMConfig)

    # ---- persistence -------------------------------------------------------

    @classmethod
    def load(cls, path: Path | None = None) -> CortexConfig:
        """Load config from a JSON file, falling back to defaults."""
        path = path or (DEFAULT_DATA_DIR / "config.json")
        if path.exists():
            with open(path) as f:
                raw = json.load(f)
            llm_raw = raw.pop("llm", {})
            cfg = cls(**{k: v for k, v in raw.items() if k != "data_dir"})
            cfg.data_dir = Path(raw.get("data_dir", DEFAULT_DATA_DIR))
            cfg.llm = LLMConfig(**llm_raw)
            return cfg
        return cls()

    def save(self, path: Path | None = None) -> None:
        """Persist current config to JSON."""
        path = path or (self.data_dir / "config.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        data["data_dir"] = str(data["data_dir"])
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ---- helpers -----------------------------------------------------------

    @property
    def knowledge_path(self) -> Path:
        return self.data_dir / self.knowledge_file

    @property
    def posts_path(self) -> Path:
        return self.data_dir / self.posts_file

    @property
    def coupons_path(self) -> Path:
        return self.data_dir / self.coupons_file
