"""SQLAlchemy implementation of CommentRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Comment
from app.infrastructure.db_models import CommentRow


def _to_domain(row: CommentRow) -> Comment:
    return Comment(
        id=row.id,
        series_id=row.series_id,
        episode_id=row.episode_id,
        content=row.content,
        created_at=row.created_at,
    )


class SqlCommentRepository:
    """Stores comments in the ``comments`` table."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a request-scoped session."""
        self._session = session

    async def add(
        self,
        *,
        series_id: int,
        episode_id: int | None,
        content: str,
    ) -> Comment:
        """Insert a comment and return it with generated fields."""
        row = CommentRow(
            series_id=series_id,
            episode_id=episode_id,
            content=content,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return _to_domain(row)

    async def list_for(
        self,
        *,
        series_id: int,
        episode_id: int | None,
    ) -> list[Comment]:
        """List comments for one target, oldest first."""
        stmt = (
            select(CommentRow)
            .where(CommentRow.series_id == series_id)
            .where(CommentRow.episode_id.is_(None))
            if episode_id is None
            else select(CommentRow)
            .where(CommentRow.series_id == series_id)
            .where(CommentRow.episode_id == episode_id)
        )
        result = await self._session.execute(
            stmt.order_by(CommentRow.created_at.asc()),
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def list_for_series_all(self, series_id: int) -> list[Comment]:
        """List every comment for a series, including episode comments."""
        stmt = (
            select(CommentRow)
            .where(CommentRow.series_id == series_id)
            .order_by(CommentRow.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [_to_domain(row) for row in result.scalars().all()]
