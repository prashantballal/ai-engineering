"""Application settings, loaded from environment variables and an optional `.env` file.

pydantic-settings reads each field from the env var with the same name (case-insensitive),
so `LOG_LEVEL=DEBUG` overrides `log_level`. Values are validated like any Pydantic model.
"""

from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    log_level: str = "INFO"

    # --- Day 3: model calls go to the LiteLLM proxy (an OpenAI-compatible API) ---
    litellm_base_url: str = "http://127.0.0.1:4000/v1"
    # The key the app sends to the proxy. Read from LITELLM_API_KEY, falling back to
    # LITELLM_MASTER_KEY, so one key in .env serves both the proxy and the app locally.
    # SecretStr keeps it out of reprs and logs.
    litellm_api_key: SecretStr = Field(
        default=SecretStr("no-key"),
        validation_alias=AliasChoices("LITELLM_API_KEY", "LITELLM_MASTER_KEY"),
    )
    # Which tier each model-backed path uses. Tier names must exist in litellm/config.yaml.
    trail_tier: str = "smart"
    general_tier: str = "fast"
    model_timeout_s: float = 60.0
    model_max_retries: int = 1
    model_max_tokens: int = 300
    model_temperature: float = 0.3

    # --- Day 5: guardrails ---
    max_input_chars: int = 1000  # longer messages get a friendly "too long" reply
    # How many characters of model output the stream guard holds back, so a pattern split
    # across chunks (an email, a phone number) is caught before any of it is sent.
    stream_holdback_chars: int = 48


@lru_cache
def get_settings() -> Settings:
    """One Settings instance per process, so the environment is read once."""
    return Settings()
