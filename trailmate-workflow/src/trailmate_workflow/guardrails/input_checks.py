"""Input guardrail rules: what we refuse to process at all, and what we clean up first.

Strictness, decided per risk:
- prompt injection and abuse → BLOCK. False positives are acceptable: a hiker rarely
  writes "ignore previous instructions".
- personal data → REDACT and continue. Punishing a user for sharing their own email
  would be hostile; the model and the logs just shouldn't see it.
- empty or too long → BLOCK, with a specific, helpful message.
"""

from dataclasses import dataclass
from typing import Literal

from trailmate_workflow.guardrails.patterns import (
    ABUSE_PATTERNS,
    INJECTION_PATTERNS,
    matching_rules,
    redact_pii,
)


@dataclass(frozen=True)
class InputVerdict:
    action: Literal["allow", "redact", "block"]
    text: str  # the text to continue with (redacted if action == "redact")
    reason: str | None = None  # why it was blocked
    rule_ids: tuple[str, ...] = ()  # which patterns matched
    redactions: tuple[str, ...] = ()  # which kinds of personal data were removed


def check_input(text: str, max_chars: int) -> InputVerdict:
    """Run the input checks in order; the first block wins."""
    text = text.strip()
    if not text:
        return InputVerdict("block", text, reason="empty")
    if len(text) > max_chars:
        return InputVerdict("block", text, reason="too_long")
    if rules := matching_rules(INJECTION_PATTERNS, text):
        return InputVerdict("block", text, reason="prompt_injection", rule_ids=rules)
    if rules := matching_rules(ABUSE_PATTERNS, text):
        return InputVerdict("block", text, reason="abusive_language", rule_ids=rules)
    redacted, kinds = redact_pii(text)
    if kinds:
        return InputVerdict("redact", redacted, redactions=kinds)
    return InputVerdict("allow", text)
