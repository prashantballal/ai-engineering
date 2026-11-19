"""Create .env with YOUR OWN LiteLLM master key. The same command on macOS, Linux and Windows:

    uv run python scripts/setup_env.py

1. If there's no .env yet, it copies .env.example to .env.
2. If .env has no LITELLM_MASTER_KEY yet, it adds one: "sk-" plus 64 random hex characters.

It's safe to run again: it never replaces a key that's already there, and it never prints
one. The key stays on this machine. On another machine, run this there; don't copy .env.
"""

import os
import secrets
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from dotenv import dotenv_values

SERVICE_DIR = Path(__file__).resolve().parent.parent  # trailmate-workflow/


def random_secret() -> str:
    return secrets.token_hex(32)  # 32 random bytes from the operating system, as hex


def ensure_env(service_dir: Path, new_secret: Callable[[], str] | None = None) -> list[str]:
    """Make sure service_dir/.env exists and holds a master key. Returns what was done."""
    env_file = service_dir / ".env"
    done = []
    if not env_file.exists():
        shutil.copyfile(service_dir / ".env.example", env_file)
        done.append("created .env from .env.example")
    if dotenv_values(env_file).get("LITELLM_MASTER_KEY"):
        done.append("LITELLM_MASTER_KEY is already set in .env, so it was left as it is")
        return done
    text = env_file.read_text(encoding="utf-8")
    with env_file.open("a", encoding="utf-8", newline="\n") as f:  # "\n" on Windows too
        if text and not text.endswith("\n"):
            f.write("\n")
        f.write(f"LITELLM_MASTER_KEY=sk-{(new_secret or random_secret)()}\n")
    if os.name != "nt":
        env_file.chmod(0o600)  # readable by you only (Windows has no such permission bits)
    done.append("added your own LITELLM_MASTER_KEY to .env (not shown: keep it private)")
    return done


def main() -> int:
    for line in ensure_env(SERVICE_DIR):
        print(f"- {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
