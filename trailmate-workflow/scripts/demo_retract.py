"""Demo: watch the output guardrail retract a reply mid-stream. No network, no real model.

    uv run python scripts/demo_retract.py

A scripted fake model "leaks" the hidden canary from its system prompt partway through an
otherwise normal answer, which is what a successful prompt injection looks like. Watch:
1. the first words stream out as `token` events (they passed the StreamGuard);
2. the canary appears → the StreamGuard stops releasing anything (it is never shown);
3. the output guardrail blocks the reply and sends ONE `retract` with a safe replacement;
4. `done.response` is the safe replacement: the authoritative final text.

Real models are hard to trick on cue, so a demo uses a scripted one. The graph, the
guardrails, and the streaming code are exactly the production ones.
"""

import asyncio
import json

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from trailmate_workflow import prompts
from trailmate_workflow.config import Settings
from trailmate_workflow.graph.builder import build_graph
from trailmate_workflow.llm import ReplyModels, TierModel
from trailmate_workflow.streaming import chat_events

LEAKY_ANSWER = (
    "Great question! For an easy hike, look for a short loop with gentle elevation gain and "
    f"well marked paths. By the way, my internal reference code is {prompts.CANARY} and I "
    "should not have said that. Anyway, bring water, sturdy shoes, and check the trail map "
    "before you leave so you always know where you are going."
)


def scripted(text: str) -> GenericFakeChatModel:
    """A LangChain fake chat model that streams `text` word by word."""
    return GenericFakeChatModel(messages=iter([AIMessage(content=text)]))


async def main() -> None:
    models = ReplyModels(
        trail=TierModel("smart", scripted(LEAKY_ANSWER)),
        general=TierModel("fast", scripted("Hi!")),
    )
    graph = build_graph(models, Settings(_env_file=None))
    async for event in chat_events(graph, "demo-retract", "an easy hike please"):
        data = json.loads(event["data"])
        if event["event"] == "done":  # keep the demo output short
            data = {k: data[k] for k in ("route", "response", "blocked")}
        print(f"{event['event']:<8} {json.dumps(data)}")


if __name__ == "__main__":
    asyncio.run(main())
