"""The patterns every guardrail shares: personal data, links, prompt injection, abuse.

Honest limits: regexes catch the obvious cases cheaply and deterministically. They are a
first layer, not a complete defence. A determined attacker can rephrase around any list
(see RESOURCES.md → Guardrails). Production systems add model-based classifiers and
dedicated PII detectors such as Microsoft Presidio.
"""

import re

# --- personal data ----------------------------------------------------------------------
# The lookbehind lets a match start only where a name starts. Without it, a long run of
# letters with no "@" is tried again from every position inside it: quadratic time.
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# North-American 10-digit numbers: NNNNNNNNNN, NNN-NNN-NNNN, (NNN) NNN NNNN, +1 NNN.NNN.NNNN.
# Digit lookarounds stop it matching a slice of a longer number (like a card).
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
# Card numbers are 13 to 19 digits, typed unbroken or in groups split by spaces or dashes.
# Other digits often sit right next to one: a pasted card, expiry date, and CVV become
# "<card> 12/26 123" once newlines turn into spaces. So instead of matching "a card", find
# each RUN of digit groups, then look for a Luhn-valid card inside it (see card_spans).
DIGIT_RUN_RE = re.compile(r"\d+(?:[ -]\d+)*")
# How cards are usually grouped: 4-4-4-4 (most cards), 4-6-5 (Amex), 4-4-4-4-3 (19 digits).
CARD_SHAPES = {(4, 4, 4, 4), (4, 6, 5), (4, 4, 4, 4, 3)}
# http(s) links and bare www. links, without trailing sentence punctuation.
URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"]*[^\s<>\".,!?;:)\]]")

PLACEHOLDERS = {"email": "[EMAIL]", "card": "[CARD]", "phone": "[PHONE]", "url": "[LINK REMOVED]"}


def luhn_valid(number: str) -> bool:
    """The Luhn checksum every real card number satisfies (it catches most typos)."""
    digits = [int(d) for d in number if d.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:  # double every second digit, starting from the right
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def card_spans(run: str) -> list[tuple[int, int]]:
    """Where card numbers sit inside a run of digit groups, as (start, end) offsets.

    1. A run of 13–19 digits that passes Luhn is one card, however it's grouped.
    2. Otherwise, scan left to right for a card in its usual shape: one unbroken group of
       13–19 digits, or consecutive groups shaped like CARD_SHAPES, that passes Luhn.
       Only whole groups count, so "<card> 12/26 123" gives back the card alone.
    """
    if 13 <= sum(char.isdigit() for char in run) <= 19 and luhn_valid(run):
        return [(0, len(run))]
    groups = [match.span() for match in re.finditer(r"\d+", run)]
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(groups):
        for j in range(i + 1, min(i + 5, len(groups)) + 1):  # stretches of 1–5 groups
            shape = tuple(end - start for start, end in groups[i:j])
            start, end = groups[i][0], groups[j - 1][1]
            unbroken = len(shape) == 1 and 13 <= shape[0] <= 19
            if (unbroken or shape in CARD_SHAPES) and luhn_valid(run[start:end]):
                spans.append((start, end))
                i = j  # carry on after this card: a run can hold more than one
                break
        else:
            i += 1
    return spans


def _redact_cards(text: str) -> tuple[str, int]:
    count = 0

    def sub(match: re.Match[str]) -> str:
        nonlocal count
        run, pieces, last = match.group(), [], 0
        for start, end in card_spans(run):
            pieces += [run[last:start], PLACEHOLDERS["card"]]
            last = end
            count += 1
        return "".join(pieces) + run[last:]

    return DIGIT_RUN_RE.sub(sub, text), count


def redact_pii(text: str) -> tuple[str, tuple[str, ...]]:
    """Replace emails, card numbers, and phone numbers with placeholders.

    Applied email → card → phone, so a phone pattern can never eat part of a card number.
    Returns the new text and the kinds that were found (in that order).
    """
    text, emails = EMAIL_RE.subn(PLACEHOLDERS["email"], text)
    text, cards = _redact_cards(text)
    text, phones = PHONE_RE.subn(PLACEHOLDERS["phone"], text)
    counts = (("email", emails), ("card", cards), ("phone", phones))
    return text, tuple(kind for kind, count in counts if count)


def redact_urls(text: str) -> tuple[str, bool]:
    """Replace links. Returns the new text and whether any link was found."""
    new_text, count = URL_RE.subn(PLACEHOLDERS["url"], text)
    return new_text, count > 0


# --- prompt injection: attempts to override the system's instructions -------------------
_I = re.IGNORECASE
INJECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    # A verb, up to five words, then a word that points at the system's OWN instructions:
    # "ignore all of your previous instructions". Hikers say "ignore the park rules" and
    # "forget the directions", so a plain "the" (or "directions") is not enough.
    "injection:ignore_instructions": re.compile(
        r"\b(?:ignore|disregard|forget|override)\b(?:\s+\S+){0,5}?\s+"
        r"(?:previous|prior|above|earlier|preceding|initial|original|all|your|system)\s+"
        r"(?:instructions?|prompts?|rules|guidelines)\b",
        _I,
    ),
    "injection:role_override": re.compile(
        r"\b(?:you are now|you're now|pretend (?:to be|you are)|roleplay as)\b", _I
    ),
    "injection:system_prompt": re.compile(r"\bsystem\s+(?:prompt|message|instructions?)\b", _I),
    # "reveal your instructions", "print the initial prompt", "repeat the instructions above".
    # "Tell me the instructions for getting a permit" has no such target, so it's allowed.
    "injection:reveal_instructions": re.compile(
        r"\b(?:reveal|show|print|repeat|tell me)\b(?:\s+\S+){0,3}?\s+"
        r"(?:(?:your|the (?:above|previous|prior|initial|original|hidden|secret))\s+(?:\S+\s+)?"
        r"(?:instructions|prompt|rules)\b|(?:instructions|prompt)\s+(?:above|you were given)\b)",
        _I,
    ),
    "injection:developer_mode": re.compile(r"\b(?:developer|dev|god|debug)\s+mode\b", _I),
    # "DAN" is case-SENSITIVE ((?-i:…)) so "my friend Dan" isn't blocked.
    "injection:jailbreak": re.compile(r"\b(?:jailbreak\w*|do anything now)\b|(?-i:\bDAN\b)", _I),
    "injection:role_tag": re.compile(
        r"<\|?\s*(?:system|im_start|im_end|assistant)\s*\|?>|#{2,}\s*system\b|\[/?INST\]", _I
    ),
}

# --- abusive language: deliberately short and crude, so judge it as a first layer only ---
_ABUSIVE = ("idiot", "moron", "dumbass", "asshole", "bitch", "fuck", "fucking", "screw you")
ABUSE_PATTERNS: dict[str, re.Pattern[str]] = {
    f"abuse:{word}": re.compile(rf"\b{re.escape(word)}\b", _I) for word in _ABUSIVE
}


def matching_rules(patterns: dict[str, re.Pattern[str]], text: str) -> tuple[str, ...]:
    """Ids of every pattern in `patterns` that matches `text`."""
    return tuple(rule_id for rule_id, pattern in patterns.items() if pattern.search(text))
