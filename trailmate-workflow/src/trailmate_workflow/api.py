"""HTTP layer: the FastAPI app, its lifespan, and routes.

Run it with:  uv run uvicorn trailmate_workflow.api:app --host 127.0.0.1 --port 8000
"""

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from langgraph.graph.state import CompiledStateGraph
from sse_starlette import EventSourceResponse

from trailmate_workflow.config import Settings, get_settings
from trailmate_workflow.graph.builder import build_graph
from trailmate_workflow.graph.state import initial_state
from trailmate_workflow.llm import make_reply_models
from trailmate_workflow.observability import log_request
from trailmate_workflow.schemas import ChatRequest, ChatResponse
from trailmate_workflow.streaming import chat_events


def get_graph(request: Request) -> CompiledStateGraph:
    """Dependency: the graph compiled once at startup. Tests override this."""
    return request.app.state.graph


GraphDep = Annotated[CompiledStateGraph, Depends(get_graph)]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Runs once at startup (before `yield`) and once at shutdown (after it).
        logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s: %(message)s")
        # Compile once and reuse: a compiled graph holds no per-request state, so all
        # requests can share it safely. Building the model clients makes no network call.
        app.state.graph = build_graph(make_reply_models(settings), settings)
        yield

    app = FastAPI(title="TrailMate workflow", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat")
    async def chat(body: ChatRequest, graph: GraphDep) -> ChatResponse:
        """Run one message through the graph and return the final state as JSON."""
        request_id = uuid.uuid4().hex
        started = time.perf_counter()
        state = await graph.ainvoke(initial_state(request_id, body.message))
        response = ChatResponse.from_state(state)
        log_request(response, started)
        return response

    @app.post("/chat/stream")
    async def chat_stream(body: ChatRequest, graph: GraphDep) -> EventSourceResponse:
        """Same graph, streamed as Server-Sent Events: start, step…, token…, done.

        sse-starlette sends a keep-alive comment every 15 s and cancels the generator
        (and so the graph run and the model call) when the client disconnects.
        """
        request_id = uuid.uuid4().hex
        return EventSourceResponse(chat_events(graph, request_id, body.message), ping=15)

    return app


app = create_app()
