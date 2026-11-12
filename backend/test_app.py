import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from . import demo, generation, main, research


def read_events(response):
    assert response.status_code == 200
    return [json.loads(line) for line in response.text.splitlines()]


def test_demo(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    client = TestClient(main.app)
    assert client.get("/api/config").json()["demo"]
    events = read_events(client.post("/api/articles", json={"topic": demo.TOPIC}))
    assert [e["stage"] for e in events if e["type"] == "stage"] == [
        "search", "review", "draft", "verify",
    ]
    sources = events[2]["sources"]
    assert [s["rank"] for s in sources] == list(range(1, 11))
    assert [s["status"] for s in sources] == ["Reviewed"] * 4 + ["Snippet only"] * 3 + ["Unavailable"] * 3
    assert "text" not in sources[0]
    assert events[-1]["type"] == "result"
    assert events[-1]["count"] == 811
    assert events[-1]["within_target"]


def test_insufficient_sources(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("SEARCH_API_KEY", "fixture")
    monkeypatch.setenv("LLM_API_KEY", "fixture")
    monkeypatch.setattr(research, "search", AsyncMock(return_value=demo.fixtures()[3:]))
    monkeypatch.setattr(research, "review", AsyncMock())
    draft = AsyncMock()
    monkeypatch.setattr(generation, "draft", draft)
    events = read_events(TestClient(main.app).post("/api/articles", json={"topic": "Weekly meals"}))
    assert len(events[-2]["sources"]) == 7
    assert "Insufficient sources" in events[-1]["message"]
    draft.assert_not_called()


@pytest.mark.parametrize("body", ["No references", "Claim [2]", "Claim [1] [99]"])
def test_citations_reject_missing_or_unreviewed_ranks(body):
    with pytest.raises(ValueError, match="Invalid citations"):
        generation.validate({**demo.article(), "body": body}, [{"rank": 1}])


def test_word_count():
    assert generation.word_count("## Quick tips\n\nDon't over-plan your week. [12]") == 6


def test_revision_runs_once(monkeypatch):
    initial = {**demo.article(), "body": "First draft [1]"}
    revised = {**demo.article(), "body": "Revised draft [1]"}
    ask = AsyncMock(side_effect=[revised, {"approved": True, "issues": []}])
    monkeypatch.setattr(generation, "ask", ask)
    result = asyncio.run(generation.verify(None, {}, initial, {"reviewed_sources": [{"rank": 1}]}))
    assert result == revised
    assert ask.await_count == 2


@pytest.mark.parametrize("url", [
    "file:///etc/hosts", "http://localhost", "http://127.0.0.1",
    "http://169.254.169.254", "http://[::ffff:127.0.0.1]",
    "https://user@example.com", "http://10.0.0.1",
])
def test_public_destinations(url):
    with pytest.raises(ValueError):
        research.checked_url(url)


def test_invalid_topic():
    assert TestClient(main.app).post("/api/articles", json={"topic": "   "}).status_code == 422


def test_redirect_to_local_is_rejected():
    class Redirect:
        status = 302
        headers = {"Location": "http://127.0.0.1/secret"}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class Session:
        requests = []

        def get(self, url, **kwargs):
            self.requests.append(str(url))
            return Redirect()

    session = Session()
    with pytest.raises(ValueError, match="Non-public"):
        asyncio.run(research.fetch(session, "https://example.org/robots.txt", robots=True))
    assert session.requests == ["https://example.org/robots.txt"]


def test_live_search_uses_organic_results_in_order():
    import httpx

    async def execute():
        def respond(request):
            assert request.url.params["gl"] == "pk"
            assert request.url.params["hl"] == "en"
            assert request.url.params["num"] == "10"
            return httpx.Response(200, json={
                "ads": [{"title": "Ad"}],
                "organic_results": [
                    {"title": f"Result {index}", "link": f"https://example.org/{index}"}
                    for index in range(12)
                ],
            })

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond), trust_env=False) as client:
            return await research.search(client, {
                "search_url": "https://provider.example/search", "search_key": "fixture",
            }, main.Brief(topic="Meal prep", country="PK"))

    sources = asyncio.run(execute())
    assert [(s["rank"], s["title"]) for s in sources] == [
        (index + 1, f"Result {index}") for index in range(10)
    ]
