"""The cross-platform helper scripts in scripts/: setup_env, run_proxy, warm_up.

They are the commands you type on Windows (which can't run the .sh scripts), and they work
the same on a Mac. Every test here is hermetic: nothing starts the proxy, nothing touches
the network, and no real key is ever made (a placeholder stands in for the secret).
"""

import importlib.util
import os
from pathlib import Path

import httpx
import pytest

from trailmate_workflow.config import Settings

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load(name: str):
    """Import scripts/<name>.py. scripts/ holds runnable files, not a package."""
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup_env = load("setup_env")
run_proxy = load("run_proxy")
warm_up = load("warm_up")


def placeholder() -> str:
    return "placeholder"


@pytest.fixture
def service(tmp_path: Path) -> Path:
    """A stand-in trailmate-workflow folder with an .env.example and no .env."""
    (tmp_path / ".env.example").write_text("LOG_LEVEL=INFO\n# LITELLM_MASTER_KEY=<yours>\n")
    return tmp_path


# --- setup_env: creates .env with your own key ---------------------------------------------


def test_setup_env_copies_the_example_and_adds_a_key(service: Path) -> None:
    done = setup_env.ensure_env(service, new_secret=placeholder)

    text = (service / ".env").read_text()
    assert text.startswith("LOG_LEVEL=INFO\n")  # copied from .env.example
    assert text.endswith("\nLITELLM_MASTER_KEY=sk-placeholder\n")
    assert any("created .env" in line for line in done)


def test_setup_env_never_replaces_a_key(service: Path) -> None:
    setup_env.ensure_env(service, new_secret=placeholder)
    before = (service / ".env").read_text()

    done = setup_env.ensure_env(service, new_secret=lambda: "another")

    assert (service / ".env").read_text() == before
    assert any("already set" in line for line in done)


def test_setup_env_puts_the_key_on_its_own_line(service: Path) -> None:
    (service / ".env").write_text("LOG_LEVEL=DEBUG")  # an existing .env with no final newline

    setup_env.ensure_env(service, new_secret=placeholder)

    assert (service / ".env").read_text() == "LOG_LEVEL=DEBUG\nLITELLM_MASTER_KEY=sk-placeholder\n"


def test_setup_env_never_prints_the_key(
    service: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(setup_env, "SERVICE_DIR", service)
    monkeypatch.setattr(setup_env, "random_secret", lambda: "placeholder-value")

    assert setup_env.main() == 0

    assert "placeholder-value" not in capsys.readouterr().out
    assert "sk-placeholder-value" in (service / ".env").read_text()


@pytest.mark.skipif(os.name == "nt", reason="POSIX file permissions")
def test_setup_env_makes_env_readable_by_you_only(service: Path) -> None:
    setup_env.ensure_env(service, new_secret=placeholder)

    assert (service / ".env").stat().st_mode & 0o777 == 0o600


# --- run_proxy: the cross-platform twin of run-proxy.sh -------------------------------------


def test_proxy_command_pins_litellm_and_its_python() -> None:
    assert run_proxy.proxy_command() == [
        "uvx", "--python", "3.12", "--from", "litellm[proxy]==1.110.0", "litellm",
        "--config", "litellm/config.yaml", "--host", "127.0.0.1", "--port", "4000",
    ]  # fmt: skip


def test_the_shell_twin_starts_the_same_proxy() -> None:
    script = (SCRIPTS / "run-proxy.sh").read_text(encoding="utf-8")

    assert "--python 3.12" in script
    assert run_proxy.LITELLM in script
    assert "LITELLM_OFFLINE_MODE" in script


def test_proxy_environment_lets_the_shell_win_over_dotenv(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("LOG_LEVEL=INFO\nFROM_FILE=yes\n")

    env = run_proxy.proxy_environment(tmp_path, {"LOG_LEVEL": "DEBUG"})

    assert env["LOG_LEVEL"] == "DEBUG"  # the app (pydantic-settings) resolves it the same way
    assert env["FROM_FILE"] == "yes"
    assert env["LITELLM_OFFLINE_MODE"] == "true"  # LiteLLM never fetches anything on its own


def test_offline_mode_can_still_be_turned_off(tmp_path: Path) -> None:
    env = run_proxy.proxy_environment(tmp_path, {"LITELLM_OFFLINE_MODE": "false"})

    assert env["LITELLM_OFFLINE_MODE"] == "false"


def must_not_start(*args, **kwargs):
    raise AssertionError("the proxy must not start")


def test_run_proxy_without_a_key_explains_and_starts_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(run_proxy, "SERVICE_DIR", tmp_path)  # no .env there
    monkeypatch.delenv("LITELLM_MASTER_KEY", raising=False)

    assert run_proxy.main(popen=must_not_start) == 1
    assert "uv run python scripts/setup_env.py" in capsys.readouterr().err


class FinishedProxy:
    def __init__(self) -> None:
        self.waits: list[float | None] = []

    def wait(self, timeout: float | None = None) -> int:
        self.waits.append(timeout)
        return 0


def test_run_proxy_starts_the_pinned_proxy_with_the_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_proxy, "SERVICE_DIR", tmp_path)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "placeholder")
    started = {}

    def popen(command, cwd, env):
        started.update(command=command, cwd=cwd, env=env)
        return FinishedProxy()

    assert run_proxy.main(popen=popen, which=lambda name: f"/bin/{name}") == 0
    assert started["command"] == run_proxy.proxy_command()
    assert started["cwd"] == tmp_path  # litellm/config.yaml is relative to it
    assert started["env"]["LITELLM_MASTER_KEY"] == "placeholder"


def test_run_proxy_can_listen_on_another_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Windows sometimes reserves a port range that includes 4000 (WinError 10013).
    monkeypatch.setattr(run_proxy, "SERVICE_DIR", tmp_path)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "placeholder")
    started = {}

    def popen(command, cwd, env):
        started["command"] = command
        return FinishedProxy()

    assert run_proxy.main(["--port", "4100"], popen=popen, which=lambda name: name) == 0
    assert started["command"][-2:] == ["--port", "4100"]


def test_run_proxy_says_so_when_uv_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(run_proxy, "SERVICE_DIR", tmp_path)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "placeholder")

    assert run_proxy.main(popen=must_not_start, which=lambda name: None) == 1
    assert "uvx" in capsys.readouterr().err


def test_ctrl_c_lets_the_proxy_finish_shutting_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_proxy, "SERVICE_DIR", tmp_path)
    monkeypatch.setenv("LITELLM_MASTER_KEY", "placeholder")
    proxy = FinishedProxy()
    first_wait = proxy.wait

    def interrupted_then_finished(timeout=None):
        if not proxy.waits:  # Ctrl+C arrives while we wait for the proxy
            proxy.waits.append(timeout)
            raise KeyboardInterrupt
        return first_wait(timeout)

    proxy.wait = interrupted_then_finished

    assert run_proxy.main(popen=lambda *a, **k: proxy, which=lambda name: name) == 0
    assert proxy.waits == [None, 15]  # waited again, with a limit, for a clean shutdown


# --- warm_up: loads both models, reading the address and key exactly as the app does -------


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("LITELLM_API_KEY", "placeholder")
    return Settings(_env_file=None)


def test_warm_asks_a_tier_for_one_token(settings: Settings) -> None:
    sent = {}

    def post(url, headers, json, timeout):
        sent.update(url=url, headers=headers, json=json)
        return httpx.Response(200, json={})

    assert warm_up.warm("smart", settings, post=post) is None
    assert sent["url"] == "http://127.0.0.1:4000/v1/chat/completions"
    assert sent["json"]["model"] == "smart"
    assert sent["json"]["max_tokens"] == 1
    assert sent["headers"]["Authorization"] == "Bearer placeholder"


@pytest.mark.parametrize(
    ("outcome", "explanation"),
    [
        (httpx.ConnectError("refused"), "uv run python scripts/run_proxy.py"),
        (httpx.ReadTimeout("slow"), "Run this again"),
        (httpx.Response(401), "same LITELLM_MASTER_KEY"),
        (httpx.Response(500), "HTTP 500"),
    ],
)
def test_warm_explains_each_failure(settings: Settings, outcome, explanation: str) -> None:
    def post(*args, **kwargs):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    assert explanation in warm_up.warm("fast", settings, post=post)


def test_warm_up_reports_every_tier_and_fails_if_one_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(warm_up, "SERVICE_DIR", tmp_path)

    def post(url, headers, json, timeout):
        return httpx.Response(200 if json["model"] == "fast" else 500)

    assert warm_up.main(post=post) == 1
    out = capsys.readouterr().out
    assert "warming fast  ... ok" in out
    assert "warming smart ... FAILED" in out
