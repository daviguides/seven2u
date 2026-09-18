"""Comment use cases."""

from app.domain.errors import ValidationError
from app.domain.interfaces import CommentRepository
from app.domain.models import Comment

MAX_COMMENT_LENGTH = 2000


class CommentService:
    """Validates and stores user comments."""

    def __init__(self, *, comment_repo: CommentRepository) -> None:
        """Inject the comment repository."""
        self._comments = comment_repo

    async def add(
        self,
        *,
        series_id: int,
        episode_id: int | None,
        content: str,
    ) -> Comment:
        """Trim and persist a comment.

        Raises:
            ValidationError: When the content is blank or too long.
        """
        cleaned = content.strip()
        if not cleaned:
            raise ValidationError("Comment must not be empty")
        if len(cleaned) > MAX_COMMENT_LENGTH:
            raise ValidationError(
                f"Comment must be at most {MAX_COMMENT_LENGTH} characters",
            )
        return await self._comments.add(
            series_id=series_id,
            episode_id=episode_id,
            content=cleaned,
        )

    async def list_for(
        self,
        *,
        series_id: int,
        episode_id: int | None,
    ) -> list[Comment]:
        """List comments for a series or one of its episodes."""
        return await self._comments.list_for(
            series_id=series_id,
            episode_id=episode_id,
        )
