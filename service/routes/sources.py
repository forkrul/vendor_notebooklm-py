"""Source endpoints (URL/text add, list, delete)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from notebooklm import NotebookLMClient

from ..auth import require_token
from ..deps import get_client
from ..models import AddTextSourceRequest, AddUrlSourceRequest, SourceOut

router = APIRouter(
    prefix="/v1/notebooks/{notebook_id}/sources",
    tags=["sources"],
    dependencies=[Depends(require_token)],
)


def _to_out(s) -> SourceOut:
    return SourceOut(
        id=getattr(s, "id", ""),
        title=getattr(s, "title", None),
        type=getattr(getattr(s, "type", None), "name", None) or str(getattr(s, "type", "") or "") or None,
        status=getattr(getattr(s, "status", None), "name", None) or str(getattr(s, "status", "") or "") or None,
    )


@router.get(
    "",
    response_model=list[SourceOut],
    summary="List sources in a notebook",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID/sources\n"
        "```"
    ),
)
async def list_sources(
    notebook_id: str, client: NotebookLMClient = Depends(get_client)
) -> list[SourceOut]:
    return [_to_out(s) for s in await client.sources.list(notebook_id)]


@router.post(
    "/url",
    response_model=SourceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a URL source (auto-detects YouTube)",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -X POST -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     -H 'Content-Type: application/json' \\\n"
        "     -d '{\"url\": \"https://example.com/article\", \"wait\": true}' \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID/sources/url\n"
        "```"
    ),
)
async def add_url_source(
    notebook_id: str,
    body: AddUrlSourceRequest,
    client: NotebookLMClient = Depends(get_client),
) -> SourceOut:
    src = await client.sources.add_url(
        notebook_id, body.url, wait=body.wait, wait_timeout=body.wait_timeout
    )
    return _to_out(src)


@router.post(
    "/text",
    response_model=SourceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a text source",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -X POST -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     -H 'Content-Type: application/json' \\\n"
        "     -d '{\"title\": \"My note\", \"content\": \"Some text...\"}' \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID/sources/text\n"
        "```"
    ),
)
async def add_text_source(
    notebook_id: str,
    body: AddTextSourceRequest,
    client: NotebookLMClient = Depends(get_client),
) -> SourceOut:
    src = await client.sources.add_text(notebook_id, body.title, body.content)
    return _to_out(src)


@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a source",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -X DELETE -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID/sources/$SRC_ID\n"
        "```"
    ),
)
async def delete_source(
    notebook_id: str, source_id: str, client: NotebookLMClient = Depends(get_client)
) -> None:
    ok = await client.sources.delete(notebook_id, source_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Delete returned False from upstream.")
