"""StreamGuard: output checks that run WHILE a reply streams.

The problem (the Day 4 + Day 5 conflict): tokens reach the client as they're generated, but
the output guardrail node only sees the reply once it's complete. Without help, an invented
email or phone number would be on screen before anything checked it.

The idea is a small HOLDBACK BUFFER: release text only when it's "settled".
1. Keep the last `holdback` characters back. Any pattern still being written lives there.
2. Only release up to a whitespace boundary, so words, emails, and links aren't cut in half.
3. Phone and card numbers CAN contain spaces ("NNN NNN NNNN"), so a whitespace boundary can
   fall inside one: move the cut back to where it starts. That new spot can itself be
   inside a link or an email ("…?b=1 2345" starts a digit run inside a link), so check all
   four kinds of match again, until the cut stops moving.
4. Redact each released segment (emails, cards, phones, links) before it leaves.
5. If a BLOCKING pattern appears (the canary, abuse), stop releasing for good. The output
   guardrail node then replaces the reply and sends a `retract`.

The cost is lag: the client sees text roughly `holdback` characters (≈ 8–10 words) behind
the model. Larger `holdback` is safer for long patterns; smaller is snappier.
LangChain's own streaming PII middleware uses the same idea with 128 characters.

Each chunk costs work in proportion to the chunk, not to the whole reply: the guard
remembers how far it has already looked. (The first version rescanned the whole reply on
every chunk. A 6,000-character reply with no spaces took over 10 seconds, and because the
guard runs on the event loop, every other request waited too.)
"""

import re

from trailmate_workflow.guardrails.patterns import (
    ABUSE_PATTERNS,
    DIGIT_RUN_RE,
    EMAIL_RE,
    PHONE_RE,
    URL_RE,
    redact_pii,
    redact_urls,
)

_WHITESPACE = re.compile(r"\s+")
_NEVER_CUT_INSIDE = (EMAIL_RE, DIGIT_RUN_RE, PHONE_RE, URL_RE)
# Blocking patterns are short (the 16-character canary, a few abusive words), so after a new
# chunk arrives only the last few characters before it can be part of a NEW match.
_BLOCK_WINDOW = 64


class StreamGuard:
    """One per model reply. Never share one between requests: it holds that reply's text."""

    def __init__(self, canary: str, holdback: int = 48) -> None:
        self._canary = canary
        self._holdback = holdback
        self._raw = ""  # everything the model has produced so far
        self._upto = 0  # raw[:_upto] has already been released
        self._released = ""  # what the client has actually been sent (redacted)
        self._block_reason: str | None = None
        self._scanned = 0  # raw[:_scanned] has already been searched for whitespace
        self._boundary = 0  # the furthest whitespace boundary found so far

    @property
    def blocked(self) -> bool:
        return self._block_reason is not None

    @property
    def block_reason(self) -> str | None:
        return self._block_reason

    @property
    def raw_text(self) -> str:
        return self._raw

    @property
    def released_text(self) -> str:
        return self._released

    def feed(self, chunk: str) -> str:
        """Add model output; return the text that's now safe to send (may be "")."""
        if self.blocked:
            return ""
        checked = len(self._raw)
        self._raw += chunk
        if reason := self._blocking_reason(start=max(0, checked - _BLOCK_WINDOW)):
            self._block_reason = reason
            return ""
        # 1 + 2: the furthest whitespace boundary that is at least `holdback` from the end.
        limit = len(self._raw) - self._holdback
        if limit > self._scanned:
            for match in _WHITESPACE.finditer(self._raw, self._scanned, limit):
                self._boundary = match.end()
            self._scanned = limit
        cut = self._boundary
        if cut <= self._upto:
            return ""  # nothing new has settled
        # 3: never cut through a match. Repeat, because moving the cut back can land it
        # inside another match. Only unreleased text can hold one, so search from _upto.
        moved = True
        while moved:
            moved = False
            for pattern in _NEVER_CUT_INSIDE:
                for match in pattern.finditer(self._raw, self._upto):
                    if match.start() < cut < match.end():
                        cut, moved = match.start(), True
        return self._release(cut)

    def flush(self) -> str:
        """The model finished: release (and redact) whatever is still held back."""
        start = max(0, len(self._raw) - _BLOCK_WINDOW)
        if not self.blocked and (reason := self._blocking_reason(start, final=True)):
            self._block_reason = reason  # e.g. the reply's very last word is abusive
        return "" if self.blocked else self._release(len(self._raw))

    def _release(self, cut: int) -> str:
        if cut <= self._upto:
            return ""
        segment, _ = redact_pii(self._raw[self._upto : cut])  # 4
        segment, _ = redact_urls(segment)
        self._upto = cut
        self._released += segment
        return segment

    def _blocking_reason(self, start: int, final: bool = False) -> str | None:
        """A blocking match that ends after `start` (everything before was checked already)."""
        if self._raw.find(self._canary, start) >= 0:
            return "canary_leak"
        for pattern in ABUSE_PATTERNS.values():
            # finditer(text, start), not finditer(text[start:]): with a slice, \b would see
            # the start of the slice as a word boundary and find "idiot" inside "bidiot".
            for match in pattern.finditer(self._raw, start):
                # Mid-stream, the end of the text so far looks like the end of a word, but
                # "idiot" may be the first half of "idiot" + "ically". Decide once at least
                # one more character has arrived, or the reply is complete (`final`).
                if final or match.end() < len(self._raw):
                    return "abusive_language"
        return None
