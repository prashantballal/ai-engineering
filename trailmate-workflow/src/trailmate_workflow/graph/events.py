"""What reply nodes push into LangGraph's *custom* stream.

`get_stream_writer()` gives the currently running node a function that sends any payload
to whoever is consuming `graph.astream(..., stream_mode=["custom", ...])`. When the graph
runs with `ainvoke` (no streaming), the writer is a harmless no-op, so the same node code
serves both `/chat` and `/chat/stream`.

Only two payload shapes exist; streaming.py turns them into SSE events:
    {"type": "token",   "text": str}                          → event: token
    {"type": "retract", "reason": str, "replacement": str}    → event: retract
"""

from langgraph.config import get_stream_writer


def emit_token(text: str) -> None:
    """Send reply text the client should show now."""
    get_stream_writer()({"type": "token", "text": text})


def emit_retract(reason: str, replacement: str) -> None:
    """Tell the client to discard all reply text shown so far and show `replacement`."""
    get_stream_writer()({"type": "retract", "reason": reason, "replacement": replacement})
