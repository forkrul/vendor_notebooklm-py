"""Notebook CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from notebooklm import NotebookLMClient, NotebookNotFoundError

from ..auth import require_token
from ..deps import get_client
from ..models import CreateNotebookRequest, NotebookOut, RenameNotebookRequest

router = APIRouter(
    prefix="/v1/notebooks",
    tags=["notebooks"],
    dependencies=[Depends(require_token)],
)


def _to_out(nb) -> NotebookOut:
    return NotebookOut(
        id=getattr(nb, "id", ""),
        title=getattr(nb, "title", "") or "",
        created_at=str(getattr(nb, "created_at", "") or "") or None,
        last_modified=str(getattr(nb, "last_modified", "") or "") or None,
    )


@router.get(
    "",
    response_model=list[NotebookOut],
    summary="List all notebooks",
    description=(
        "Returns every notebook visible to the authenticated NotebookLM account.\n\n"
        "**curl**:\n"
        "```bash\n"
        "curl -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     http://localhost:8000/v1/notebooks\n"
        "```"
    ),
)
async def list_notebooks(client: NotebookLMClient = Depends(get_client)) -> list[NotebookOut]:
    return [_to_out(nb) for nb in await client.notebooks.list()]


@router.post(
    "",
    response_model=NotebookOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notebook",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -X POST -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     -H 'Content-Type: application/json' \\\n"
        "     -d '{\"title\": \"My new notebook\"}' \\\n"
        "     http://localhost:8000/v1/notebooks\n"
        "```"
    ),
)
async def create_notebook(
    body: CreateNotebookRequest, client: NotebookLMClient = Depends(get_client)
) -> NotebookOut:
    return _to_out(await client.notebooks.create(body.title))


@router.get(
    "/{notebook_id}",
    response_model=NotebookOut,
    summary="Get a single notebook",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID\n"
        "```"
    ),
)
async def get_notebook(
    notebook_id: str, client: NotebookLMClient = Depends(get_client)
) -> NotebookOut:
    try:
        return _to_out(await client.notebooks.get(notebook_id))
    except NotebookNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch(
    "/{notebook_id}",
    response_model=NotebookOut,
    summary="Rename a notebook",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -X PATCH -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     -H 'Content-Type: application/json' \\\n"
        "     -d '{\"title\": \"Renamed notebook\"}' \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID\n"
        "```"
    ),
)
async def rename_notebook(
    notebook_id: str,
    body: RenameNotebookRequest,
    client: NotebookLMClient = Depends(get_client),
) -> NotebookOut:
    return _to_out(await client.notebooks.rename(notebook_id, body.title))


@router.delete(
    "/{notebook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notebook",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -X DELETE -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID\n"
        "```"
    ),
)
async def delete_notebook(
    notebook_id: str, client: NotebookLMClient = Depends(get_client)
) -> None:
    ok = await client.notebooks.delete(notebook_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Delete returned False from upstream.")
