"""Bearer-token gate for the service.

Reads `API_TOKEN` from the environment. If unset, the service refuses to start —
we never want an unprotected listener exposing NotebookLM credentials.
"""

from __future__ import annotations

import hmac
import os
import secrets

from fastapi import Header, HTTPException, status


def _expected_token() -> str:
    token = os.environ.get("API_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "API_TOKEN is not set. Generate one with `openssl rand -hex 32` "
            "and put it in the service `.env` file."
        )
    return token


def require_token(authorization: str | None = Header(default=None)) -> None:
    """FastAPI dependency: validates `Authorization: Bearer <token>`."""
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header (expected 'Bearer <token>').",
            headers={"WWW-Authenticate": "Bearer"},
        )
    presented = authorization.split(" ", 1)[1].strip()
    expected = _expected_token()
    # constant-time compare
    if not hmac.compare_digest(presented.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API token.",
        )


def random_token() -> str:
    """Helper for generating a new API token (used by `python -m service.auth`)."""
    return secrets.token_hex(32)


if __name__ == "__main__":
    print(random_token())
