"""Guardrails as first-class graph citizens: ordinary nodes, wired in with ordinary edges.

    receive → input_guardrail ─(blocked)→ blocked_reply ─┐
                              └(allowed)→ classify → … ──┴→ output_guardrail → respond

The rules themselves live in guardrails/ (plain functions). These nodes apply them to the
state, record a trace step, and (for the output guardrail) correct the stream if needed.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from trailmate_workflow import templates
from trailmate_workflow.graph.events import emit_retract, emit_token
from trailmate_workflow.graph.state import TrailState, trace_step
from trailmate_workflow.guardrails.input_checks import check_input
from trailmate_workflow.guardrails.output_checks import check_output

Node = Callable[[TrailState], Awaitable[dict[str, Any]]]


def make_input_guardrail(max_chars: int) -> Node:
    """Check the normalized text before anything else sees it: block, redact, or allow."""

    async def input_guardrail(state: TrailState) -> dict[str, Any]:
        started = time.perf_counter()
        verdict = check_input(state["text"], max_chars)
        update: dict[str, Any] = {
            "input_verdict": verdict.action,
            "blocked": verdict.action == "block",
        }
        details: dict[str, Any] = {}
        if verdict.action == "block":
            update["block_reason"] = verdict.reason
            details = {"reason": verdict.reason, "rules": list(verdict.rule_ids)}
        elif verdict.action == "redact":
            update["text"] = verdict.text  # everything downstream sees the redacted text
            details = {"redactions": list(verdict.redactions)}
        update["trace"] = [trace_step("input_guardrail", verdict.action, started, **details)]
        return update

    return input_guardrail


def make_blocked_reply(max_chars: int) -> Node:
    """The reply for a blocked message: a fixed template per block reason."""

    async def blocked_reply(state: TrailState) -> dict[str, Any]:
        started = time.perf_counter()
        reason = state["block_reason"]
        reply = templates.BLOCKED_REPLIES[reason].format(max_chars=max_chars)
        emit_token(reply)
        return {
            "reply": reply,
            "streamed_text": reply,
            "tier": None,
            "model": None,
            "fallback_used": False,
            "trace": [trace_step("blocked_reply", reason, started)],
        }

    return blocked_reply


def make_output_guardrail(canary: str) -> Node:
    """Check every complete reply, templated ones included, and fix the stream if needed.

    If the checked text differs from what the client was already sent, the client must be
    corrected: `retract` replaces text it has shown; if it was shown nothing yet, the final
    text is simply sent as a token.
    """

    async def output_guardrail(state: TrailState) -> dict[str, Any]:
        started = time.perf_counter()
        verdict = check_output(state["reply"], canary)
        streamed = state.get("streamed_text", "")
        if verdict.text != streamed:
            if streamed:
                emit_retract(verdict.reason or "redacted", verdict.text)
            else:
                emit_token(verdict.text)
        details: dict[str, Any] = {}
        if verdict.reason:
            details["reason"] = verdict.reason
        if verdict.redactions:
            details["redactions"] = list(verdict.redactions)
        return {
            "reply": verdict.text,
            "streamed_text": verdict.text,
            "output_verdict": verdict.action,
            "trace": [trace_step("output_guardrail", verdict.action, started, **details)],
        }

    return output_guardrail
