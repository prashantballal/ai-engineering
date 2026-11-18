"""Model-backed reply nodes: the ONLY place a model is involved, and only to write text.

The routing decision was already made (by plain code) before these nodes run. If the
model call fails for any reason, the node falls back to a fixed template, and that
fallback decision is code, not a model.

Day 4: the node streams, pushing text to the client (emit_token) as the model writes it.
Day 5: every chunk goes through a StreamGuard first. Only text the guard has checked and
released ever reaches the client, and the guard can stop the stream entirely.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.messages import AIMessageChunk, HumanMessage, SystemMessage

from trailmate_workflow.graph.events import emit_retract, emit_token
from trailmate_workflow.graph.state import TrailState, trace_step
from trailmate_workflow.guardrails.stream_guard import StreamGuard
from trailmate_workflow.llm import TierModel, model_name_from

Node = Callable[[TrailState], Awaitable[dict[str, Any]]]


def make_model_reply_node(
    node_name: str,
    tier_model: TierModel,
    system_prompt: str,
    fallback_reply: str,
    *,
    canary: str,
    holdback: int,
) -> Node:
    """Build a node that streams `tier_model`'s reply through a StreamGuard.

    A factory (a function that returns the node) lets one implementation serve every
    model-backed path, each with its own tier, prompt, and fallback.
    """

    async def model_reply(state: TrailState) -> dict[str, Any]:
        started = time.perf_counter()
        messages = [SystemMessage(system_prompt), HumanMessage(state["text"])]
        guard = StreamGuard(canary, holdback)  # a new guard per call: never shared
        full: AIMessageChunk | None = None  # chunks added together (`+`) = the whole message
        try:
            async for chunk in tier_model.model.astream(messages):
                full = chunk if full is None else full + chunk
                if released := guard.feed(chunk.text):
                    emit_token(released)
                if guard.blocked:
                    break  # stop paying for a reply that will be replaced anyway
            if tail := guard.flush():
                emit_token(tail)
        except Exception as exc:  # proxy down, timeout, bad response, …: degrade, don't crash
            # (asyncio.CancelledError is a BaseException, so a client disconnect still
            # cancels the run instead of being swallowed here.)
            if guard.released_text:
                # The client already shows part of a reply: tell it to replace that text.
                emit_retract("model_error", fallback_reply)
            else:
                emit_token(fallback_reply)
            return {
                "reply": fallback_reply,
                "streamed_text": fallback_reply,
                "tier": tier_model.tier,
                "model": None,
                "fallback_used": True,
                "trace": [
                    trace_step(
                        node_name,
                        "fallback",
                        started,
                        tier=tier_model.tier,
                        error=type(exc).__name__,
                    )
                ],
            }
        model = model_name_from(full) if full is not None else None
        details: dict[str, Any] = {"tier": tier_model.tier, "model": model}
        if guard.blocked:
            details["stopped"] = guard.block_reason
        return {
            # The FULL, unchecked reply: the output guardrail checks it next. It never goes
            # to the client as-is: only `step` metadata and the checked final text do.
            "reply": guard.raw_text,
            "streamed_text": guard.released_text,  # exactly what the client has seen
            "tier": tier_model.tier,
            "model": model,
            "fallback_used": False,
            "trace": [trace_step(node_name, "generated", started, **details)],
        }

    model_reply.__name__ = node_name
    return model_reply
