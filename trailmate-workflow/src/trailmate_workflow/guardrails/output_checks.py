"""Output guardrail rules: checked on every complete reply, templated ones included.

Strictness, decided per risk:
- system-prompt leak (the canary appears) → BLOCK: the model was manipulated.
- abusive language → BLOCK.
- personal data → REDACT: the model has no real data, so any email or phone number is
  invented (or echoed back), and is never something we want to show.
- links → REDACT: there is no trail database yet, so any URL the model writes is made up.
- empty reply → replace it with a fixed fallback.
"""

from dataclasses import dataclass
from typing import Literal

from trailmate_workflow import templates
from trailmate_workflow.guardrails.patterns import (
    ABUSE_PATTERNS,
    matching_rules,
    redact_pii,
    redact_urls,
)


@dataclass(frozen=True)
class OutputVerdict:
    action: Literal["pass", "redact", "block"]
    text: str  # the text the user should finally see
    reason: str | None = None
    redactions: tuple[str, ...] = ()


def check_output(text: str, canary: str) -> OutputVerdict:
    """Check a complete reply; the first block wins, otherwise redact what needs it."""
    if not text.strip():
        return OutputVerdict("block", templates.EMPTY_REPLY_FALLBACK, reason="empty_reply")
    if canary in text:
        return OutputVerdict("block", templates.OUTPUT_BLOCKED_REPLY, reason="canary_leak")
    if matching_rules(ABUSE_PATTERNS, text):
        return OutputVerdict("block", templates.OUTPUT_BLOCKED_REPLY, reason="abusive_language")
    redacted, kinds = redact_pii(text)
    redacted, had_url = redact_urls(redacted)
    kinds = kinds + (("url",) if had_url else ())
    if kinds:
        return OutputVerdict("redact", redacted, redactions=kinds)
    return OutputVerdict("pass", text)
