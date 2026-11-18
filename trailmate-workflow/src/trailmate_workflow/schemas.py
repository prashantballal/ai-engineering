"""Request and response bodies: the HTTP contract, as Pydantic models."""

from typing import Any

from pydantic import BaseModel, Field

from trailmate_workflow.graph.state import TrailState


class ChatRequest(BaseModel):
    # min_length=1 rejects "" with a 422 before the graph ever runs. max_length is a hard
    # cap on payload size; the friendlier "message too long" reply is a guardrail (Day 5).
    message: str = Field(min_length=1, max_length=10_000)


class TraceStepOut(BaseModel):
    node: str
    outcome: str
    details: dict[str, Any]
    duration_ms: float


class ChatResponse(BaseModel):
    request_id: str
    response: str
    route: str | None = None  # which path the graph took
    tier: str | None = None  # the tier requested for this path (None = no model involved)
    model: str | None = None  # the model that actually answered
    fallback_used: bool = False  # the model failed and a fixed template was returned
    blocked: bool = False  # the input guardrail refused the message
    trace: list[TraceStepOut]

    @classmethod
    def from_state(cls, state: TrailState) -> "ChatResponse":
        """Build the API response from the graph's final state."""
        blocked = bool(state.get("blocked"))
        return cls(
            request_id=state["request_id"],
            response=state["response"],
            route="blocked" if blocked else state.get("category"),
            blocked=blocked,
            tier=state.get("tier"),
            model=state.get("model"),
            fallback_used=state.get("fallback_used", False),
            trace=state["trace"],
        )
