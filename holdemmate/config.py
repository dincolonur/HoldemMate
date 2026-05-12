"""Configuration: env + Streamlit-secrets loading.

Settings are read from (in order of precedence):
1. Streamlit secrets (`st.secrets["KEY"]`) — used on Streamlit Community Cloud
   when the secret is set in the app's *Secrets* UI.
2. Environment variables (loaded from `.env` locally via python-dotenv).
3. The default value passed in code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is optional in production
    pass


def _read(key: str, default: str | None = None) -> str | None:
    """Read a config value, preferring Streamlit secrets, then env vars."""
    # st.secrets only works inside a Streamlit run, and raises if no
    # secrets.toml is configured locally. Catch broadly so we silently fall
    # back to env vars in tests, scripts, and local dev.
    try:
        import streamlit as st  # type: ignore

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    model: str
    mc_trials: int
    app_password: str | None  # If set, the Streamlit UI is gated behind this.

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            anthropic_api_key=_read("ANTHROPIC_API_KEY"),
            # Default to Haiku for speed/cost. Override via env or Streamlit secret
            # for stronger reasoning at the cost of latency:
            #   HOLDEMMATE_MODEL=claude-sonnet-4-6
            #   HOLDEMMATE_MODEL=claude-opus-4-6
            model=_read("HOLDEMMATE_MODEL", "claude-haiku-4-5-20251001")
            or "claude-haiku-4-5-20251001",
            mc_trials=int(_read("HOLDEMMATE_MC_TRIALS", "2000") or "2000"),
            app_password=_read("APP_PASSWORD"),
        )


def get_settings() -> Settings:
    return Settings.from_env()
