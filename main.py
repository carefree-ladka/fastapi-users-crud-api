"""Compatibility shim.

The application now lives in the ``app`` package. Prefer running:

    uvicorn app.main:app --reload

This re-export keeps ``uvicorn main:app`` working as well.
"""
from app.main import app

__all__ = ["app"]
