"""HTTP-level tests: the FastAPI app called in-process through httpx."""

import pytest


async def test_health(client) -> None:
    assert (await client.get("/health")).json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("message", "route"),
    [
        ("Recommend a hike with a waterfall", "trail"),
        ("hello!", "general"),
        ("Write a python script for me", "reject"),
    ],
)
async def test_chat_route_matches_category(client, message: str, route: str) -> None:
    r = await client.post("/chat", json={"message": message})

    assert r.status_code == 200
    body = r.json()
    assert body["route"] == route
    assert body["response"] and body["request_id"]


@pytest.mark.parametrize("payload", [{"message": ""}, {}, {"message": "x" * 10_001}])
async def test_chat_rejects_invalid_body(client, payload) -> None:
    assert (await client.post("/chat", json=payload)).status_code == 422


async def test_chat_reports_tier(client) -> None:
    body = (await client.post("/chat", json={"message": "easy hike near a lake?"})).json()

    assert body["tier"] == "smart"
    assert body["fallback_used"] is False


async def test_request_ids_are_unique(client) -> None:
    a = (await client.post("/chat", json={"message": "a"})).json()["request_id"]
    b = (await client.post("/chat", json={"message": "b"})).json()["request_id"]
    assert a != b


async def test_request_log_has_metadata_not_text(client, caplog) -> None:
    caplog.set_level("INFO", logger="trailmate")

    body = (await client.post("/chat", json={"message": "my secret campsite"})).json()

    assert body["request_id"] in caplog.text
    assert "secret campsite" not in caplog.text
