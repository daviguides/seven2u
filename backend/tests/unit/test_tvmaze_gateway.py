import httpx
import pytest

from app.domain.errors import NotFoundError, UpstreamError
from app.infrastructure.tvmaze_gateway import TVMazeGateway, strip_html

SHOW = {
    "id": 169,
    "name": "Breaking Bad",
    "genres": ["Drama", "Crime"],
    "premiered": "2008-01-20",
    "status": "Ended",
    "rating": {"average": 9.2},
    "image": {"medium": "m.jpg", "original": "o.jpg"},
    "summary": "<p>A <b>teacher</b> &amp; a student.</p>",
}

EPISODE = {
    "id": 1,
    "season": 1,
    "number": 1,
    "name": "Pilot",
    "airdate": "2008-01-20",
    "runtime": 60,
    "image": None,
    "summary": None,
}


def gateway_with(handler):
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://t")
    return TVMazeGateway(client=client)


def test_strip_html_removes_tags_and_unescapes():
    assert strip_html("<p>A <b>x</b> &amp; y</p>") == "A x & y"
    assert strip_html(None) is None
    assert strip_html("<p></p>") is None


async def test_gateway_search_maps_shows():
    def handler(request):
        assert request.url.params["q"] == "bad"
        return httpx.Response(200, json=[{"score": 1, "show": SHOW}])

    gateway = gateway_with(handler)

    results = await gateway.search("bad")

    assert results[0].name == "Breaking Bad"
    assert results[0].summary == "A teacher & a student."
    assert results[0].image_url == "o.jpg"
    assert results[0].rating == 9.2


async def test_gateway_episodes_tolerate_missing_fields():
    gateway = gateway_with(lambda r: httpx.Response(200, json=[EPISODE]))

    episodes = await gateway.get_episodes(169)

    assert episodes[0].series_id == 169
    assert episodes[0].summary is None
    assert episodes[0].image_url is None


async def test_gateway_404_raises_not_found():
    gateway = gateway_with(lambda r: httpx.Response(404, json={}))

    with pytest.raises(NotFoundError):
        await gateway.get_series(999)


async def test_gateway_5xx_raises_upstream():
    gateway = gateway_with(lambda r: httpx.Response(503, text="down"))

    with pytest.raises(UpstreamError):
        await gateway.get_series(1)


async def test_gateway_caches_responses():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=SHOW)

    gateway = gateway_with(handler)

    await gateway.get_series(169)
    await gateway.get_series(169)

    assert calls == 1
