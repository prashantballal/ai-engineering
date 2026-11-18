"""The graph's state: the single dict every node reads from and writes partial updates to."""

import operator
import time
from typing import Annotated, Any, TypedDict

from trailmate_workflow.classifier import Category


class TraceStep(TypedDict):
    """One entry in a run's trace. Metadata only, never user text or model text."""

    node: str
    outcome: str
    details: dict[str, Any]
    duration_ms: float


class TrailState(TypedDict, total=False):
    """Everything one request carries through the graph.

    `total=False` means no key is required up front: nodes add keys as the run goes.
    """

    request_id: str
    message: str  # the raw message exactly as received; never logged or traced
    text: str  # the working copy every rule reads: normalized (and, from Day 5, redacted)
    reply: str  # the draft reply produced by a reply node
    response: str  # the final text returned to the client

    # A *reducer*. By default, a key a node returns REPLACES the old value. With
    # Annotated[list, operator.add], LangGraph instead combines old + new, so when a node
    # returns {"trace": [step]} its step is APPENDED. That is how every node adds its own entry.
    trace: Annotated[list[TraceStep], operator.add]

    # Day 2: set by the `classify` node and read by the routing function.
    category: Category
    matched_rules: list[str]

    # Day 3: set by the reply nodes.
    tier: str | None  # the tier the app REQUESTED (part of the deterministic routing)
    model: str | None  # the model that ACTUALLY answered, as reported by the proxy
    fallback_used: bool  # True when the model call failed and a fixed template was used

    # Day 5: guardrails.
    input_verdict: str  # allow | redact | block
    blocked: bool  # the input guardrail refused to process the message
    block_reason: str | None  # empty | too_long | prompt_injection | abusive_language
    streamed_text: str  # exactly the reply text already sent to the client
    output_verdict: str  # pass | redact | block


def trace_step(node: str, outcome: str, started: float, **details: Any) -> TraceStep:
    """Build a trace step. `started` is the time.perf_counter() value from when the node began."""
    return {
        "node": node,
        "outcome": outcome,
        "details": details,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def initial_state(request_id: str, message: str) -> TrailState:
    """The input for one graph run."""
    return {"request_id": request_id, "message": message, "trace": []}
