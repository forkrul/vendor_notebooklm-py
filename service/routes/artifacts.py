"""Artifact (audio/video/etc.) generation endpoints.

This is intentionally a small surface — only audio is wired up here as a
representative example. Other artifact types follow the same pattern; add as
needed.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from notebooklm import AudioLength, NotebookLMClient

from ..auth import require_token
from ..deps import get_client
from ..models import ArtifactOut, ArtifactStatusOut, GenerateAudioRequest

router = APIRouter(
    prefix="/v1/notebooks/{notebook_id}/artifacts",
    tags=["artifacts"],
    dependencies=[Depends(require_token)],
)


@router.get(
    "",
    response_model=list[ArtifactOut],
    summary="List artifacts (audio/video/reports/etc.) for a notebook",
    description=(
        "**curl**:\n"
        "```bash\n"
        "curl -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID/artifacts\n"
        "```"
    ),
)
async def list_artifacts(
    notebook_id: str, client: NotebookLMClient = Depends(get_client)
) -> list[ArtifactOut]:
    items = await client.artifacts.list(notebook_id)
    out: list[ArtifactOut] = []
    for a in items:
        out.append(
            ArtifactOut(
                id=getattr(a, "id", ""),
                type=getattr(getattr(a, "type", None), "name", None)
                or str(getattr(a, "type", "") or "")
                or None,
                title=getattr(a, "title", None),
                status=getattr(getattr(a, "status", None), "name", None)
                or str(getattr(a, "status", "") or "")
                or None,
            )
        )
    return out


@router.post(
    "/audio",
    response_model=ArtifactStatusOut,
    summary="Trigger audio (podcast) generation",
    description=(
        "Kicks off podcast-style audio generation. The response carries a task id;\n"
        "poll `GET /v1/notebooks/{notebook_id}/artifacts` to see when it finishes.\n\n"
        "**curl**:\n"
        "```bash\n"
        "curl -X POST -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     -H 'Content-Type: application/json' \\\n"
        "     -d '{\"length\": \"DEFAULT\"}' \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID/artifacts/audio\n"
        "```"
    ),
)
async def generate_audio(
    notebook_id: str,
    body: GenerateAudioRequest,
    client: NotebookLMClient = Depends(get_client),
) -> ArtifactStatusOut:
    kwargs: dict = {}
    if body.length:
        try:
            kwargs["length"] = AudioLength[body.length.upper()]
        except KeyError as e:
            valid = ", ".join(m.name for m in AudioLength)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid length '{body.length}'. Valid: {valid}",
            ) from e
    status = await client.artifacts.generate_audio(notebook_id, **kwargs)
    return ArtifactStatusOut(
        task_id=getattr(status, "task_id", None),
        status=getattr(getattr(status, "status", None), "name", None)
        or str(getattr(status, "status", "") or "")
        or None,
        artifact_id=getattr(status, "artifact_id", None),
    )
