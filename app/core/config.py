"""Application configuration.

Settings are plain values with sane defaults and can be overridden via
environment variables (or a local .env file). Kept dependency-light (no
pydantic-settings) on purpose.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load variables from a local .env file into the environment (if present).
# Existing environment variables always take precedence over .env values.
load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "RAG API"
    version: str = "0.1.0"
    description: str = "Local-first AI API."
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./app.db"

    # --- Auth / security ---
    # Secret used to sign JWTs. MUST be overridden via SECRET_KEY in any real
    # deployment; the default is only for local development.
    secret_key: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    # Cookie behaviour. Set cookie_secure=True (HTTPS) in production.
    cookie_secure: bool = False
    cookie_samesite: str = "lax"  # one of: lax, strict, none
    cookie_domain: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance, allowing env overrides."""
    return Settings(
        app_name=os.getenv("APP_NAME", "RAG API"),
        version=os.getenv("APP_VERSION", "0.1.0"),
        description=os.getenv("APP_DESCRIPTION", "Local-first AI API."),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./app.db"),
        secret_key=os.getenv("SECRET_KEY", "dev-insecure-change-me"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_ttl_minutes=int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "15")),
        refresh_token_ttl_days=int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "7")),
        cookie_secure=_env_bool("COOKIE_SECURE", False),
        cookie_samesite=os.getenv("COOKIE_SAMESITE", "lax"),
        cookie_domain=os.getenv("COOKIE_DOMAIN") or None,
    )
