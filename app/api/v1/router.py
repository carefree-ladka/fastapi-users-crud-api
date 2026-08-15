"""Aggregates all v1 routers into a single router.

Mounted under the configured API prefix (default: /api/v1) in app.main.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.routers import health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
