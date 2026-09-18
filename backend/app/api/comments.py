"""Comment endpoints for series and episodes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_comment_service
from app.api.schemas import CommentIn, CommentOut
from app.services.comment_service import CommentService

router = APIRouter(prefix="/series/{series_id}/comments", tags=["comments"])

CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
EpisodeQuery = Annotated[int | None, Query(ge=1)]


@router.get("", response_model=list[CommentOut])
async def list_comments(
    series_id: int,
    service: CommentServiceDep,
    episode_id: EpisodeQuery = None,
) -> list[CommentOut]:
    """List comments for the series, or for one episode when given."""
    comments = await service.list_for(
        series_id=series_id,
        episode_id=episode_id,
    )
    return [CommentOut.from_domain(c) for c in comments]


@router.post(
    "",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    series_id: int,
    body: CommentIn,
    service: CommentServiceDep,
    episode_id: EpisodeQuery = None,
) -> CommentOut:
    """Create a comment on the series or one of its episodes."""
    comment = await service.add(
        series_id=series_id,
        episode_id=episode_id,
        content=body.content,
    )
    return CommentOut.from_domain(comment)
