"""Load both tiers' models into memory before a demo. The same command on macOS, Linux, Windows:

    uv run python scripts/warm_up.py

The first request after a model has been unloaded pays a cold start: several seconds, and
longer on a CPU. This pays it up front. The proxy address and key are read exactly the way
the app reads them (Settings: your shell first, then .env), so "ok" here means the app will
get through too. The cross-platform twin of warm-up.sh.
"""

import sys
from collections.abc import Callable
from pathlib import Path

import httpx

from trailmate_workflow.config import Settings

SERVICE_DIR = Path(__file__).resolve().parent.parent  # trailmate-workflow/
TIERS = ("fast", "smart")

Post = Callable[..., httpx.Response]


def warm(tier: str, settings: Settings, post: Post | None = None) -> str | None:
    """Ask `tier` for a single token. None means it worked; otherwise, why it didn't."""
    base_url = settings.litellm_base_url.rstrip("/")
    try:
        response = (post or httpx.post)(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.litellm_api_key.get_secret_value()}"},
            json={"model": tier, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
            timeout=180,  # loading a model from disk onto a CPU can take a while
        )
    except httpx.ConnectError:
        return f"no proxy at {base_url}. Start it first: uv run python scripts/run_proxy.py"
    except httpx.TimeoutException:
        return "timed out while the model was loading. Run this again"
    if response.status_code == 401:
        return "the proxy rejected the key. The app and the proxy need the same LITELLM_MASTER_KEY"
    if response.is_error:
        return f"HTTP {response.status_code} from the proxy. Its terminal shows why"
    return None


def main(post: Post | None = None) -> int:
    settings = Settings(_env_file=SERVICE_DIR / ".env")
    failed = False
    for tier in TIERS:
        print(f"warming {tier:<5} ... ", end="", flush=True)
        reason = warm(tier, settings, post)
        print("ok" if reason is None else f"FAILED: {reason}")
        failed = failed or reason is not None
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
