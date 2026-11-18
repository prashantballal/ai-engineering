"""Day 4: the SSE endpoint and the event protocol.

httpx's ASGITransport buffers the whole response body, which is fine here: every stream
ends after `done` (or `error`). Tests parse the body with the same parser the CLI uses.
"""

import json

from helpers import ScriptedChatModel, client_for, events_of, graph_with

from trailmate_workflow import templates
from trailmate_workflow.graph.state import initial_state
from trailmate_workflow.sse import SSEEvent, parse_sse
from trailmate_workflow.streaming import chat_events


async def stream(graph, message: str) -> list[SSEEvent]:
    async with client_for(graph) as client:
        response = await client.post("/chat/stream", json={"message": message})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    return events_of(response.text)


def tokens(events: list[SSEEvent]) -> list[str]:
    return [e.data["text"] for e in events if e.event == "token"]


def test_parse_sse_handles_comments_multiline_and_default_event() -> None:
    lines = [": ping", "event: token", 'data: {"text": "hi"}', "", 'data: {"a":', "data: 1}", ""]

    assert list(parse_sse(lines)) == [
        SSEEvent("token", {"text": "hi"}),
        SSEEvent("message", {"a": 1}),
    ]


LONG_REPLY = [f"word{i} " for i in range(30)]  # ~180 chars: streams past the 48-char holdback


async def test_model_path_streams_many_tokens() -> None:
    events = await stream(graph_with(trail=ScriptedChatModel(chunks=LONG_REPLY)), "easy hike?")

    assert events[0].event == "start" and events[-1].event == "done"
    assert len(tokens(events)) > 1  # arrives in several pieces, not all at the end
    assert "".join(tokens(events)) == events[-1].data["response"] == "".join(LONG_REPLY)
    assert [e.data["node"] for e in events if e.event == "step"] == [
        "receive",
        "input_guardrail",
        "classify",
        "trail_reply",
        "output_guardrail",
        "respond",
    ]


async def test_short_reply_is_held_back_and_sent_once_complete() -> None:
    """Day 5 trade-off: text within the guard's holdback is only sent once it's safe."""
    trail = ScriptedChatModel(chunks=["Try ", "the ", "lakeside ", "loop."])

    events = await stream(graph_with(trail=trail), "easy hike?")

    assert tokens(events) == ["Try the lakeside loop."]


async def test_templated_path_sends_exactly_one_token() -> None:
    events = await stream(graph_with(), "write python code")

    assert tokens(events) == [events[-1].data["response"]]
    assert events[-1].data["route"] == "reject"


async def test_steps_never_carry_reply_text() -> None:
    trail = ScriptedChatModel(chunks=["Try ", "the ", "lakeside ", "loop."])

    events = await stream(graph_with(trail=trail), "easy hike?")

    assert all("lakeside" not in json.dumps(e.data) for e in events if e.event == "step")


async def test_model_failure_before_any_token_sends_fallback_as_one_token() -> None:
    failing = ScriptedChatModel(chunks=[], fail_after=0)

    events = await stream(graph_with(trail=failing), "easy hike?")

    assert tokens(events) == [templates.TRAIL_FALLBACK_REPLY]
    assert not [e for e in events if e.event == "retract"]
    assert events[-1].data["fallback_used"] is True


async def test_model_failure_mid_stream_retracts() -> None:
    # Enough text is released before the failure that the client has something to replace.
    partial = ScriptedChatModel(chunks=LONG_REPLY, fail_after=20)

    events = await stream(graph_with(trail=partial), "easy hike?")

    retracts = [e for e in events if e.event == "retract"]
    assert len(retracts) == 1
    assert retracts[0].data == {
        "reason": "model_error",
        "replacement": templates.TRAIL_FALLBACK_REPLY,
    }
    assert events[-1].data["response"] == templates.TRAIL_FALLBACK_REPLY


async def test_unexpected_error_yields_error_event() -> None:
    class BrokenGraph:
        async def astream(self, *args, **kwargs):
            raise RuntimeError("boom")
            yield  # pragma: no cover  (makes this an async generator)

    names = [e["event"] async for e in chat_events(BrokenGraph(), "r", "hi")]

    assert names == ["start", "error"]


async def test_chat_events_aclose_mid_stream_is_clean() -> None:
    """A client that disconnects mid-stream must not break the shared graph."""
    graph = graph_with()
    events = chat_events(graph, "r", "easy hike?")
    async for event in events:
        if event["event"] == "token":
            break
    await events.aclose()  # what the server does when the client goes away

    assert (await graph.ainvoke(initial_state("r2", "hello")))["response"]
