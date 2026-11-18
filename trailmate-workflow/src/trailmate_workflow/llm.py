"""Model clients: one LangChain chat model per TIER, all pointed at the LiteLLM proxy.

The app never names a real model. It asks the proxy for a tier ("fast" or "smart"), and
litellm/config.yaml decides which Ollama model answers. Swapping models is a config change.
"""

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from trailmate_workflow.config import Settings


@dataclass(frozen=True)
class TierModel:
    tier: str  # the tier name, recorded in state and trace (the routing decision)
    model: BaseChatModel  # anything LangChain-compatible: ChatOpenAI in prod, a fake in tests


@dataclass(frozen=True)
class ReplyModels:
    trail: TierModel
    general: TierModel


def make_chat_model(tier: str, settings: Settings) -> ChatOpenAI:
    """A ChatOpenAI client that talks to the LiteLLM proxy and requests `tier` as the model."""
    return ChatOpenAI(
        model=tier,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_api_key,
        timeout=settings.model_timeout_s,
        max_retries=settings.model_max_retries,
        max_tokens=settings.model_max_tokens,
        temperature=settings.model_temperature,
    )


def make_reply_models(settings: Settings) -> ReplyModels:
    """Build the clients for each model-backed path. No network call happens here."""
    return ReplyModels(
        trail=TierModel(settings.trail_tier, make_chat_model(settings.trail_tier, settings)),
        general=TierModel(settings.general_tier, make_chat_model(settings.general_tier, settings)),
    )


def model_name_from(message: BaseMessage) -> str | None:
    """The model that ACTUALLY answered, as reported by the server.

    The tier is what we asked for; this is what we got. If LiteLLM falls back from
    "smart" to "fast", the tier still says "smart" but this reveals the real model.
    """
    return message.response_metadata.get("model_name")
