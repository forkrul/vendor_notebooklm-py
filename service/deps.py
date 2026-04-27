"""Shared NotebookLMClient lifecycle and FastAPI dependency.

A single client is reused across requests (httpx connection pool, cached CSRF
token, etc.). It is created on app startup via the lifespan handler in main.py
and torn down on shutdown.
"""

from __future__ import annotations

import os

from fastapi import HTTPException, Request, status

from notebooklm import NotebookLMClient


async def make_client() -> NotebookLMClient:
    """Construct a client from the mounted storage_state.

    Storage path resolution order:
    1. `NOTEBOOKLM_STORAGE_PATH` (explicit file path)
    2. `NOTEBOOKLM_HOME/storage_state.json`
    3. Library default (`~/.notebooklm/storage_state.json`)
    """
    explicit = os.environ.get("NOTEBOOKLM_STORAGE_PATH")
    if explicit:
        return await NotebookLMClient.from_storage(path=explicit)
    return await NotebookLMClient.from_storage()


def get_client(request: Request) -> NotebookLMClient:
    """FastAPI dependency: returns the shared client from app state."""
    client = getattr(request.app.state, "nlm_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NotebookLM client not initialized — check service logs.",
        )
    return client
