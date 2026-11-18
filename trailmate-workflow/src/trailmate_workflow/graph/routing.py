"""Routing functions for conditional edges.

A routing function reads the state and returns the NAME of the next node. It's ordinary
code: no model decides where a request goes. The `Literal[...]` return type lists every
possible destination, so LangGraph can validate the edges and draw the branches.
"""

from typing import Literal

from trailmate_workflow.graph.state import TrailState

ReplyNode = Literal["trail_reply", "general_reply", "reject_reply"]

_REPLY_NODE_FOR: dict[str, ReplyNode] = {
    "trail": "trail_reply",
    "general": "general_reply",
    "reject": "reject_reply",
}


def route_after_input(state: TrailState) -> Literal["blocked_reply", "classify"]:
    """input_guardrail → blocked_reply if it blocked the message, otherwise on to classify."""
    return "blocked_reply" if state.get("blocked") else "classify"


def route_by_category(state: TrailState) -> ReplyNode:
    """classify → one reply node per category."""
    return _REPLY_NODE_FOR[state["category"]]
