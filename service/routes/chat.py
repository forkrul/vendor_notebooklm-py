"""Chat endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from notebooklm import NotebookLMClient

from ..auth import require_token
from ..deps import get_client
from ..models import AskRequest, AskResponse, CitationOut

router = APIRouter(
    prefix="/v1/notebooks/{notebook_id}/chat",
    tags=["chat"],
    dependencies=[Depends(require_token)],
)


@router.post(
    "",
    response_model=AskResponse,
    summary="Ask a question against a notebook's sources",
    description=(
        "Returns the model's answer plus extracted citations. Pass "
        "`conversation_id` from a previous response to continue a conversation.\n\n"
        "**curl**:\n"
        "```bash\n"
        "curl -X POST -H \"Authorization: Bearer $API_TOKEN\" \\\n"
        "     -H 'Content-Type: application/json' \\\n"
        "     -d '{\"question\": \"Summarise the main argument.\"}' \\\n"
        "     http://localhost:8000/v1/notebooks/$NB_ID/chat\n"
        "```"
    ),
)
async def ask(
    notebook_id: str,
    body: AskRequest,
    client: NotebookLMClient = Depends(get_client),
) -> AskResponse:
    result = await client.chat.ask(
        notebook_id,
        body.question,
        source_ids=body.source_ids,
        conversation_id=body.conversation_id,
    )
    citations: list[CitationOut] = []
    for c in getattr(result, "references", []) or []:
        citations.append(
            CitationOut(
                source_id=getattr(c, "source_id", None),
                text=getattr(c, "text", None),
                start=getattr(c, "start", None),
                end=getattr(c, "end", None),
            )
        )
    return AskResponse(
        answer=getattr(result, "answer", "") or "",
        conversation_id=getattr(result, "conversation_id", None),
        citations=citations,
    )
