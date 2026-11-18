"""Graph-level tests: run the compiled LangGraph graph directly, without HTTP."""

import json

import pytest
from helpers import graph_with

from trailmate_workflow import templates
from trailmate_workflow.classifier import REJECT_TOPICS
from trailmate_workflow.graph.state import initial_state


@pytest.mark.parametrize(
    ("message", "route", "reply_node"),
    [
        ("Recommend a hike with a waterfall", "trail", "trail_reply"),
        ("hello!", "general", "general_reply"),
        ("Write a python script for me", "reject", "reject_reply"),
    ],
)
async def test_each_category_takes_its_own_path(message: str, route: str, reply_node: str) -> None:
    state = await graph_with().ainvoke(initial_state("r", message))

    assert state["category"] == route
    assert [s["node"] for s in state["trace"]] == [
        "receive",
        "input_guardrail",
        "classify",
        reply_node,
        "output_guardrail",
        "respond",
    ]


async def test_reject_reply_names_the_topic() -> None:
    state = await graph_with().ainvoke(initial_state("r", "Should I invest in bitcoin?"))

    assert state["response"] == templates.REJECT_REPLY.format(topic=REJECT_TOPICS["reject:finance"])


async def test_classify_step_records_the_matched_rules() -> None:
    state = await graph_with().ainvoke(initial_state("r", "easy hike near a lake?"))

    classify_step = next(s for s in state["trace"] if s["node"] == "classify")
    assert classify_step["outcome"] == "trail"
    assert classify_step["details"]["rules"] == ["trail:kw:hike", "trail:kw:lake"]


async def test_trace_never_contains_message_or_reply_text() -> None:
    state = await graph_with().ainvoke(initial_state("req-2", "secret plans for saturday"))

    trace_json = json.dumps(state["trace"])
    assert "secret plans" not in trace_json
    assert state["reply"] not in trace_json
