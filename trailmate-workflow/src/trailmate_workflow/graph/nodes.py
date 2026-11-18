"""Graph nodes.

A node is a (here: async) function that receives the current state and returns a
*partial update*: only the keys it wants to change. LangGraph merges that update into
the state, using each key's reducer if it has one (see `trace` in state.py).
"""

import time
from typing import Any

from trailmate_workflow import templates
from trailmate_workflow.classifier import classify as classify_text
from trailmate_workflow.graph.events import emit_token
from trailmate_workflow.graph.state import TrailState, trace_step
from trailmate_workflow.normalize import normalize_text


async def receive(state: TrailState) -> dict[str, Any]:
    """Entry node: turn the raw message into the normalized working `text`."""
    started = time.perf_counter()
    text = normalize_text(state["message"])
    return {"text": text, "trace": [trace_step("receive", "normalized", started, chars=len(text))]}


async def classify(state: TrailState) -> dict[str, Any]:
    """Decide the category with plain rules. The routing function reads `category` next."""
    started = time.perf_counter()
    result = classify_text(state["text"])
    rules = list(result.matched_rules)
    return {
        "category": result.category,
        "matched_rules": rules,
        "trace": [trace_step("classify", result.category, started, rules=rules)],
    }


# Day 3: trail_reply and general_reply became model-backed nodes (graph/model_nodes.py).
# Their Day 2 templates live on as the fallbacks used when the model can't be reached.


async def reject_reply(state: TrailState) -> dict[str, Any]:
    """Out-of-scope requests get a fixed, polite refusal. Never a model.

    Day 4: a template has no tokens to stream, so it's sent as ONE token event: honest,
    and the client handles it exactly like a model reply. (No fake "typing".)
    """
    started = time.perf_counter()
    reply = templates.render_reject(state["matched_rules"])
    emit_token(reply)
    return {
        "reply": reply,
        "streamed_text": reply,
        "tier": None,
        "model": None,
        "fallback_used": False,
        "trace": [trace_step("reject_reply", "templated", started)],
    }


async def respond(state: TrailState) -> dict[str, Any]:
    """Response node: the reply becomes the final response."""
    started = time.perf_counter()
    return {"response": state["reply"], "trace": [trace_step("respond", "responded", started)]}
