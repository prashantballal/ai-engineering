"""Live tests against the real LiteLLM proxy + Ollama. Skipped unless RUN_INTEGRATION=1.

./scripts/run-proxy.sh            # in another terminal (needs LITELLM_MASTER_KEY in .env)
RUN_INTEGRATION=1 uv run pytest -m integration -q     # 4 live tests
"""

import os

import pytest
from helpers import client_for, events_of

from trailmate_workflow.config import Settings
from trailmate_workflow.graph.builder import build_graph
from trailmate_workflow.llm import make_chat_model, make_reply_models

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("RUN_INTEGRATION") != "1",
        reason="set RUN_INTEGRATION=1 with the LiteLLM proxy and Ollama running",
    ),
]


@pytest.mark.parametrize("tier", ["fast", "smart"])
async def test_each_tier_answers(tier: str) -> None:
    reply = await make_chat_model(tier, Settings()).ainvoke("Say hi in three words.")

    assert reply.text.strip()


async def test_trail_message_end_to_end() -> None:
    settings = Settings()
    async with client_for(build_graph(make_reply_models(settings), settings)) as client:
        body = (await client.post("/chat", json={"message": "easy hike near a lake?"})).json()

    assert body["route"] == "trail"
    assert body["fallback_used"] is False
    # `model` must name the model that actually answered, not echo the tier we asked for.
    # If this fails, LiteLLM reports the tier alias: see BUILD-GUIDE "Closing the live
    # proxy check" for reading the real model from its response headers instead.
    assert body["model"] not in (None, body["tier"])


async def test_trail_reply_streams_in_many_tokens() -> None:
    settings = Settings()
    async with client_for(build_graph(make_reply_models(settings), settings)) as client:
        response = await client.post("/chat/stream", json={"message": "easy hike near a lake?"})
    events = events_of(response.text)

    assert len([e for e in events if e.event == "token"]) > 1  # really streamed, not one block
    assert events[-1].event == "done"
    assert events[-1].data["route"] == "trail"
