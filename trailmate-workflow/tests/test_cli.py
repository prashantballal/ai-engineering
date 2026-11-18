"""Tests for the `trailmate` command-line tool."""

import io

from trailmate_workflow.cli import EventPrinter, main
from trailmate_workflow.sse import SSEEvent


def render(events: list[SSEEvent]) -> str:
    out = io.StringIO()
    printer = EventPrinter(out)
    for event in events:
        printer(event)
    return out.getvalue()


def test_cli_graph_prints_mermaid(capsys) -> None:
    assert main(["graph"]) == 0

    out = capsys.readouterr().out
    assert "classify" in out and "reject_reply" in out


def test_printer_shows_steps_tokens_and_summary() -> None:
    text = render(
        [
            SSEEvent(
                "step",
                {
                    "node": "classify",
                    "outcome": "trail",
                    "details": {"rules": ["trail:kw:hike"]},
                    "duration_ms": 0.1,
                },
            ),
            SSEEvent("token", {"text": "Try "}),
            SSEEvent("token", {"text": "this."}),
            SSEEvent(
                "done",
                {"route": "trail", "tier": "smart", "model": "m", "fallback_used": False},
            ),
        ]
    )

    assert "classify" in text and "trail:kw:hike" in text
    assert "Try this." in text  # tokens are printed inline, as they arrive
    assert "route=trail" in text and "tier=smart" in text


def test_printer_starts_a_new_line_for_a_step_after_tokens() -> None:
    text = render(
        [
            SSEEvent("token", {"text": "Try this."}),
            SSEEvent(
                "step",
                {"node": "trail_reply", "outcome": "generated", "details": {}, "duration_ms": 1},
            ),
        ]
    )

    assert "Try this.\n" in text


def test_printer_shows_retract_replacement() -> None:
    text = render(
        [
            SSEEvent("token", {"text": "Partial "}),
            SSEEvent("retract", {"reason": "model_error", "replacement": "Fixed reply."}),
        ]
    )

    assert "replaced" in text and "model_error" in text and "Fixed reply." in text


def test_chat_exits_1_when_api_unreachable(capsys) -> None:
    assert main(["chat", "hi", "--url", "http://127.0.0.1:9"]) == 1

    assert "not reachable" in capsys.readouterr().out
