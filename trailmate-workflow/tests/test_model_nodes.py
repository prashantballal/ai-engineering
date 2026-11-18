"""Day 3: the trail and general paths call a model (through its tier); reject never does."""

from helpers import ScriptedChatModel, graph_with, step

from trailmate_workflow import templates
from trailmate_workflow.graph.state import initial_state


async def test_trail_path_uses_smart_tier() -> None:
    state = await graph_with().ainvoke(initial_state("r", "easy hike near a lake?"))

    assert (state["reply"], state["tier"], state["fallback_used"]) == (
        "Trail answer.",
        "smart",
        False,
    )
    assert step(state, "trail_reply")["outcome"] == "generated"


async def test_general_path_uses_fast_tier() -> None:
    state = await graph_with().ainvoke(initial_state("r", "hello"))

    assert (state["reply"], state["tier"]) == ("Hello hiker!", "fast")


async def test_model_receives_system_prompt_and_normalized_text() -> None:
    trail = ScriptedChatModel(chunks=["ok"])
    await graph_with(trail=trail).ainvoke(initial_state("r", "  easy   hike? "))

    system, human = trail.seen[0]
    assert system.type == "system" and "TrailMate" in system.content
    assert human.type == "human" and human.content == "easy hike?"


async def test_reject_path_calls_no_model() -> None:
    failing = ScriptedChatModel(chunks=[], fail_after=0)
    state = await graph_with(failing, failing).ainvoke(initial_state("r", "write python code"))

    assert state["tier"] is None and state["fallback_used"] is False
    assert failing.seen == []


async def test_model_failure_falls_back_to_template() -> None:
    failing = ScriptedChatModel(chunks=[], fail_after=0)
    state = await graph_with(trail=failing).ainvoke(initial_state("r", "easy hike?"))

    assert state["reply"] == templates.TRAIL_FALLBACK_REPLY
    assert state["fallback_used"] is True
    assert step(state, "trail_reply")["outcome"] == "fallback"
    assert step(state, "trail_reply")["details"]["error"] == "ConnectionError"
