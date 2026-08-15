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


@dataclass(frozen=True)
class Settings:
    app_name: str = "RAG API"
    version: str = "0.1.0"
    description: str = "Local-first AI API."
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./app.db"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance, allowing env overrides."""
    return Settings(
        app_name=os.getenv("APP_NAME", "RAG API"),
        version=os.getenv("APP_VERSION", "0.1.0"),
        description=os.getenv("APP_DESCRIPTION", "Local-first AI API."),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./app.db"),
    )
