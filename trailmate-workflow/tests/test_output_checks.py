"""Day 5: the output guardrail's rules for a complete reply."""

import pytest
from fake_pii import FAKE_EMAIL, FAKE_PHONE_SPACED

from trailmate_workflow import templates
from trailmate_workflow.guardrails.output_checks import check_output
from trailmate_workflow.prompts import CANARY


@pytest.mark.parametrize(
    ("text", "action", "reason", "kinds"),
    [
        ("Try the lakeside loop.", "pass", None, ()),
        ("   ", "block", "empty_reply", ()),
        (f"My reference is {CANARY}.", "block", "canary_leak", ()),
        ("You absolute idiot", "block", "abusive_language", ()),
        (f"Contact the ranger at {FAKE_EMAIL}", "redact", None, ("email",)),
        ("See https://trails.example.org/mist for details", "redact", None, ("url",)),
        (f"Call {FAKE_PHONE_SPACED} or visit www.example.org", "redact", None, ("phone", "url")),
    ],
)
def test_check_output(text: str, action: str, reason: str | None, kinds: tuple[str, ...]) -> None:
    verdict = check_output(text, CANARY)

    assert (verdict.action, verdict.reason, verdict.redactions) == (action, reason, kinds)


def test_pass_keeps_text_and_blocks_replace_it() -> None:
    assert check_output("Try the lakeside loop.", CANARY).text == "Try the lakeside loop."
    assert check_output(f"ref {CANARY}", CANARY).text == templates.OUTPUT_BLOCKED_REPLY
    assert check_output("", CANARY).text == templates.EMPTY_REPLY_FALLBACK


def test_redaction_replaces_values_with_placeholders() -> None:
    verdict = check_output(f"Mail {FAKE_EMAIL} or see https://x.example.org/a", CANARY)

    assert verdict.text == "Mail [EMAIL] or see [LINK REMOVED]"


def test_canary_is_in_every_system_prompt() -> None:
    from trailmate_workflow import prompts

    assert CANARY in prompts.TRAIL_SYSTEM_PROMPT and CANARY in prompts.GENERAL_SYSTEM_PROMPT
