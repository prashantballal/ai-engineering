"""Day 3: how tiers become chat-model clients pointed at the LiteLLM proxy."""

from langchain_core.messages import AIMessage

from trailmate_workflow.config import Settings
from trailmate_workflow.llm import make_chat_model, make_reply_models, model_name_from


def test_make_chat_model_targets_proxy_tier() -> None:
    model = make_chat_model("smart", Settings(_env_file=None))

    assert model.model_name == "smart"  # the TIER name; LiteLLM maps it to a real model
    assert model.openai_api_base == "http://127.0.0.1:4000/v1"
    assert (model.max_tokens, model.max_retries) == (300, 1)


def test_paths_map_to_tiers_from_settings() -> None:
    models = make_reply_models(Settings(_env_file=None, trail_tier="fast", general_tier="smart"))

    assert (models.trail.tier, models.general.tier) == ("fast", "smart")


def test_api_key_falls_back_to_master_key(monkeypatch) -> None:
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "test-key-not-secret")

    model = make_chat_model("fast", Settings(_env_file=None))

    assert model.openai_api_key.get_secret_value() == "test-key-not-secret"


def test_model_name_from_reads_metadata() -> None:
    message = AIMessage("x", response_metadata={"model_name": "ollama_chat/qwen3:4b-instruct"})

    assert model_name_from(message) == "ollama_chat/qwen3:4b-instruct"
    assert model_name_from(AIMessage("x")) is None
