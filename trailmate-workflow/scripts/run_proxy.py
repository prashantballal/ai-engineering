"""Start the LiteLLM proxy on http://127.0.0.1:4000. The same command on macOS, Linux, Windows:

    uv run python scripts/run_proxy.py

The cross-platform twin of run-proxy.sh (Windows can't run .sh scripts):
1. It reads .env, but a variable already set in your shell wins, exactly as it does for the
   app (pydantic-settings). So the app and the proxy always agree on the key.
2. It stops with a clear message if there's no LITELLM_MASTER_KEY. (LiteLLM refuses to start
   without one too, less helpfully.)
3. It runs the pinned LiteLLM as an isolated uv tool on Python 3.12, so every machine runs the
   same proxy, with LITELLM_OFFLINE_MODE=true, so the proxy never downloads anything on its
   own. It only talks to Ollama.

Ctrl+C stops it.
"""

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from dotenv import dotenv_values

SERVICE_DIR = Path(__file__).resolve().parent.parent  # trailmate-workflow/
LITELLM = "litellm[proxy]==1.110.0"  # keep in step with run-proxy.sh
TOOL_PYTHON = "3.12"  # LiteLLM's own Python, separate from the app's 3.14

NO_KEY = (
    "LITELLM_MASTER_KEY is not set, and LiteLLM won't start without one.\n"
    "Create your own key once (it goes into .env and stays on this machine):\n"
    "  uv run python scripts/setup_env.py\n"
)


def proxy_command(port: int = 4000) -> list[str]:
    return [
        "uvx", "--python", TOOL_PYTHON, "--from", LITELLM, "litellm",
        "--config", "litellm/config.yaml", "--host", "127.0.0.1", "--port", str(port),
    ]  # fmt: skip


def proxy_environment(service_dir: Path, environ: Mapping[str, str]) -> dict[str, str]:
    """Variables from .env, overridden by the shell's own, with offline mode on by default."""
    from_file = {k: v for k, v in dotenv_values(service_dir / ".env").items() if v is not None}
    return {"LITELLM_OFFLINE_MODE": "true", **from_file, **environ}


def main(
    argv: Sequence[str] = (),
    popen: Callable[..., subprocess.Popen] | None = None,
    which=shutil.which,
) -> int:
    parser = argparse.ArgumentParser(description="Start the LiteLLM proxy for TrailMate.")
    parser.add_argument(
        "--port",
        type=int,
        default=4000,
        help="port to listen on (default 4000). If you change it, set LITELLM_BASE_URL in "
        ".env to match, e.g. http://127.0.0.1:4100/v1",
    )
    args = parser.parse_args(argv)
    env = proxy_environment(SERVICE_DIR, os.environ)
    if not env.get("LITELLM_MASTER_KEY"):
        print(NO_KEY, end="", file=sys.stderr)
        return 1
    if which("uvx") is None:
        print(
            "uvx not found. Install uv (see the run guide), then open a new terminal.",
            file=sys.stderr,
        )
        return 1
    process = (popen or subprocess.Popen)(proxy_command(args.port), cwd=SERVICE_DIR, env=env)
    try:
        return process.wait()
    except KeyboardInterrupt:  # Ctrl+C reached the proxy too: give it time to shut down cleanly
        try:
            return process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
