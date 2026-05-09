"""Configuration: env loading + model defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is optional in production
    pass


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    model: str
    mc_trials: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("HOLDEMMATE_MODEL", "claude-sonnet-4-6"),
            mc_trials=int(os.getenv("HOLDEMMATE_MC_TRIALS", "2000")),
        )


def get_settings() -> Settings:
    return Settings.from_env()
