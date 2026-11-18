"""Turn one graph run into a sequence of SSE events.

    start → step (per node, as it finishes) → token… / retract → done      (or → error)

We consume three LangGraph stream modes at once, using the v2 output format, where every
item is a self-describing dict {"type", "ns", "data"}:

- "updates": after each node finishes, {node_name: the partial update it returned}.
             We forward ONLY the new trace step(s), so reply text never leaks into `step`.
- "custom":  whatever nodes pushed with get_stream_writer(): reply tokens and retracts.
- "values":  the full state after each step. We keep the last one to build `done`.
"""

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from trailmate_workflow.graph.state import initial_state
from trailmate_workflow.observability import log_request
from trailmate_workflow.schemas import ChatResponse

logger = logging.getLogger("trailmate")

GENERIC_ERROR = "Something went wrong. Please try again."


def _event(name: str, payload: dict[str, Any]) -> dict[str, str]:
    """An event in the dict shape sse-starlette's EventSourceResponse accepts."""
    return {"event": name, "data": json.dumps(payload)}


async def chat_events(graph: Any, request_id: str, message: str) -> AsyncIterator[dict[str, str]]:
    """Run the graph for one message and yield SSE events as things happen."""
    started = time.perf_counter()
    yield _event("start", {"request_id": request_id})

    final_state = None
    try:
        async for part in graph.astream(
            initial_state(request_id, message),
            stream_mode=["updates", "custom", "values"],
            version="v2",
        ):
            kind, data = part["type"], part["data"]
            if kind == "updates":
                for update in data.values():
                    for step in (update or {}).get("trace", []):
                        yield _event("step", step)
            elif kind == "custom":
                yield _event(data["type"], {k: v for k, v in data.items() if k != "type"})
            elif kind == "values":
                final_state = data
    except Exception as exc:
        # Metadata only in the log line; the full traceback only at DEBUG level.
        logger.error("stream failed request_id=%s error=%s", request_id, type(exc).__name__)
        logger.debug("stream failure traceback", exc_info=True)
        yield _event("error", {"message": GENERIC_ERROR})
        return

    response = ChatResponse.from_state(final_state)
    log_request(response, started)
    yield _event("done", response.model_dump())
