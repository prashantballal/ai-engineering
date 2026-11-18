"""Wire the nodes into a graph and compile it."""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from trailmate_workflow import prompts, templates
from trailmate_workflow.config import Settings
from trailmate_workflow.graph import nodes
from trailmate_workflow.graph.guardrail_nodes import (
    make_blocked_reply,
    make_input_guardrail,
    make_output_guardrail,
)
from trailmate_workflow.graph.model_nodes import make_model_reply_node
from trailmate_workflow.graph.routing import route_after_input, route_by_category
from trailmate_workflow.graph.state import TrailState
from trailmate_workflow.llm import ReplyModels

REPLY_NODES = ("trail_reply", "general_reply", "reject_reply")


def build_graph(models: ReplyModels, settings: Settings) -> CompiledStateGraph:
    """The complete Phase 1 workflow.

    START → receive → input_guardrail ─(blocked)→ blocked_reply ──────────────┐
                                      └(allowed)→ classify ─(category)→ reply ─┴→
          output_guardrail → respond → END

    `models` is injected (rather than created here) so tests can pass fakes and the app
    can pass real proxy clients. The graph's SHAPE never depends on which models are used.
    """
    stream_guard = {"canary": prompts.CANARY, "holdback": settings.stream_holdback_chars}
    graph = StateGraph(TrailState)

    graph.add_node("receive", nodes.receive)
    graph.add_node("input_guardrail", make_input_guardrail(settings.max_input_chars))
    graph.add_node("blocked_reply", make_blocked_reply(settings.max_input_chars))
    graph.add_node("classify", nodes.classify)
    graph.add_node(
        "trail_reply",
        make_model_reply_node(
            "trail_reply",
            models.trail,
            prompts.TRAIL_SYSTEM_PROMPT,
            templates.TRAIL_FALLBACK_REPLY,
            **stream_guard,
        ),
    )
    graph.add_node(
        "general_reply",
        make_model_reply_node(
            "general_reply",
            models.general,
            prompts.GENERAL_SYSTEM_PROMPT,
            templates.GENERAL_FALLBACK_REPLY,
            **stream_guard,
        ),
    )
    graph.add_node("reject_reply", nodes.reject_reply)
    graph.add_node("output_guardrail", make_output_guardrail(prompts.CANARY))
    graph.add_node("respond", nodes.respond)

    graph.add_edge(START, "receive")
    graph.add_edge("receive", "input_guardrail")
    # Two conditional edges, both decided by plain code:
    graph.add_conditional_edges("input_guardrail", route_after_input, ["blocked_reply", "classify"])
    graph.add_conditional_edges("classify", route_by_category, list(REPLY_NODES))
    # Every reply, templated or generated, blocked or not, passes the output guardrail.
    for reply_node in (*REPLY_NODES, "blocked_reply"):
        graph.add_edge(reply_node, "output_guardrail")
    graph.add_edge("output_guardrail", "respond")
    graph.add_edge("respond", END)

    return graph.compile()
