"""Test helpers shared by several test modules (imported as `from helpers import ...`)."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langgraph.graph.state import CompiledStateGraph
from pydantic import Field

from trailmate_workflow.api import create_app, get_graph
from trailmate_workflow.config import Settings
from trailmate_workflow.graph.builder import build_graph
from trailmate_workflow.graph.state import TraceStep, TrailState
from trailmate_workflow.llm import ReplyModels, TierModel
from trailmate_workflow.sse import SSEEvent, parse_sse

# Defaults only: a developer's .env must not change test behaviour.
TEST_SETTINGS = Settings(_env_file=None)


@asynccontextmanager
async def client_for(graph: CompiledStateGraph) -> AsyncIterator[httpx.AsyncClient]:
    """An HTTP client wired to a fresh app that uses `graph`.

    httpx's ASGITransport calls the app in-process: no server, no network. It does NOT
    run the app's lifespan, so instead of relying on startup code we override the
    `get_graph` dependency, the FastAPI-idiomatic way to inject test doubles.
    """
    app = create_app()
    app.dependency_overrides[get_graph] = lambda: graph
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class ScriptedChatModel(BaseChatModel):
    """A fake chat model with a script: it streams fixed `chunks`, and can fail on cue.

    - fail_after=None: never fails.
    - fail_after=N: streams N chunks, then raises ConnectionError (0 = fails immediately).
      A non-streaming call (ainvoke) with any fail_after set raises straight away.
    - seen: every message list it was called with, so tests can check what the model got.
    """

    chunks: list[str]
    fail_after: int | None = None
    seen: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs: Any):
        self.seen.append(list(messages))
        if self.fail_after is not None:
            raise ConnectionError("proxy unreachable")
        message = AIMessage(content="".join(self.chunks))
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _astream(
        self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs: Any
    ) -> AsyncIterator[ChatGenerationChunk]:
        self.seen.append(list(messages))
        for i, text in enumerate(self.chunks):
            if self.fail_after is not None and i >= self.fail_after:
                raise ConnectionError("proxy unreachable")
            await asyncio.sleep(0)  # yield control, like a real network stream would
            yield ChatGenerationChunk(message=AIMessageChunk(content=text))
        if self.fail_after is not None and self.fail_after >= len(self.chunks):
            raise ConnectionError("proxy unreachable")


def make_models(
    trail: BaseChatModel | None = None, general: BaseChatModel | None = None
) -> ReplyModels:
    """ReplyModels with scripted fakes on the real tier names ("smart" / "fast")."""
    return ReplyModels(
        trail=TierModel("smart", trail or ScriptedChatModel(chunks=["Trail ", "answer."])),
        general=TierModel("fast", general or ScriptedChatModel(chunks=["Hello ", "hiker!"])),
    )


def graph_with(
    trail: BaseChatModel | None = None,
    general: BaseChatModel | None = None,
    settings: Settings = TEST_SETTINGS,
) -> CompiledStateGraph:
    """The real graph, with scripted fake models and default settings."""
    return build_graph(make_models(trail, general), settings)


def step(state: TrailState, node: str) -> TraceStep:
    """The trace step a given node recorded."""
    return next(s for s in state["trace"] if s["node"] == node)


def steps_named(state: TrailState) -> Iterator[str]:
    return (s["node"] for s in state["trace"])


def events_of(body: str) -> list[SSEEvent]:
    """Parse a complete SSE response body into events (same parser the CLI uses)."""
    return list(parse_sse(body.splitlines()))
