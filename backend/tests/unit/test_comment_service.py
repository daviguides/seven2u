import pytest

from app.domain.errors import ValidationError
from app.services.comment_service import MAX_COMMENT_LENGTH, CommentService


@pytest.fixture
def service(comment_repo):
    return CommentService(comment_repo=comment_repo)


async def test_comment_service_trims_content(service):
    comment = await service.add(series_id=1, episode_id=None, content="  hi ")

    assert comment.content == "hi"
    assert comment.episode_id is None


@pytest.mark.parametrize("content", ["", "   ", "\n\t"])
async def test_comment_service_rejects_blank(service, content):
    with pytest.raises(ValidationError):
        await service.add(series_id=1, episode_id=None, content=content)


async def test_comment_service_rejects_too_long(service):
    with pytest.raises(ValidationError):
        await service.add(
            series_id=1,
            episode_id=None,
            content="x" * (MAX_COMMENT_LENGTH + 1),
        )


async def test_comment_service_separates_series_and_episode_targets(
    service,
):
    await service.add(series_id=1, episode_id=None, content="series")
    await service.add(series_id=1, episode_id=11, content="episode")

    series_comments = await service.list_for(series_id=1, episode_id=None)
    episode_comments = await service.list_for(series_id=1, episode_id=11)

    assert [c.content for c in series_comments] == ["series"]
    assert [c.content for c in episode_comments] == ["episode"]


async def test_comment_service_lists_in_insertion_order(service):
    await service.add(series_id=1, episode_id=None, content="first")
    await service.add(series_id=1, episode_id=None, content="second")

    comments = await service.list_for(series_id=1, episode_id=None)

    assert [c.content for c in comments] == ["first", "second"]
