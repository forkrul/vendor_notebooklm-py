"""FastAPI entry point.

Exposes the notebooklm-py client as a small REST API with Swagger UI at /docs.
Authentication is via `Authorization: Bearer $API_TOKEN`. The underlying
NotebookLM credentials come from a Playwright `storage_state.json` mounted into
the container — never bake them into the image.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .deps import make_client
from .routes import artifacts, chat, notebooks, sources

logger = logging.getLogger("notebooklm.service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate API_TOKEN early so misconfigured deployments fail loudly.
    from .auth import _expected_token
    _expected_token()

    logger.info("Starting NotebookLM client …")
    client = await make_client()
    app.state.nlm_client = client
    try:
        yield
    finally:
        logger.info("Closing NotebookLM client …")
        await client.close()


app = FastAPI(
    title="notebooklm-py service",
    version=os.environ.get("SERVICE_VERSION", "0.1.0"),
    description=(
        "Thin REST/Swagger wrapper around the [notebooklm-py](https://github.com/teng-lin/notebooklm-py) "
        "client. Every endpoint is gated by `Authorization: Bearer $API_TOKEN`. "
        "NotebookLM auth comes from a Playwright `storage_state.json` mounted at "
        "`/data/storage_state.json` (or via `NOTEBOOKLM_HOME`)."
    ),
    lifespan=lifespan,
)


@app.get("/healthz", tags=["meta"], summary="Liveness probe")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(notebooks.router)
app.include_router(sources.router)
app.include_router(chat.router)
app.include_router(artifacts.router)
