"""Rule-based message classification: plain code, no model, fully deterministic.

Every rule is data: an id plus a compiled regex. `classify` checks the rule groups in a
fixed priority order and returns the first group that matches:

    reject  →  trail  →  general  →  default (general)

Reject goes first so the system *fails closed*: a message that mentions a trail but asks
for something out of scope ("write a Python script to scrape trail data") is rejected.
A message that matches nothing goes to `general`, which is still a rule, not a guess.

All patterns use word boundaries (\\b), so "hi" matches "hi!" but not "this" or "hiking".
"""

import re
from dataclasses import dataclass
from typing import Literal

Category = Literal["trail", "general", "reject"]


@dataclass(frozen=True)
class Classification:
    category: Category
    matched_rules: tuple[str, ...]  # rule ids, e.g. ("trail:kw:hike", "trail:kw:lake")


def _rule(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


# Out-of-scope requests: "we don't do that here". (Safety blocking is a separate job: the
# Day 5 input guardrail.) Kept deliberately narrow, to avoid rejecting real hiking questions
# like "what's the function of trekking poles?" or "how do I avoid poison ivy?". A rule
# fires on what is being ASKED FOR, not on a word that merely appears. The final review
# found five rules that broke this; test_classifier.py keeps the sentences that proved it.
_NOW = (
    r"(?:today|tonight|tomorrow|now|currently|current|live"
    r"|this (?:week|weekend)|next (?:week|weekend))"
)
REJECT_RULES: dict[str, re.Pattern[str]] = {
    # A coding verb near a code word. Not "program": "a training program" is fitness.
    "reject:code": _rule(
        r"\b(?:write|writing|debug|fix|generate|refactor)\b.{0,40}"
        r"\b(?:code|script|function|regex|sql|python|javascript|typescript|java)\b"
        r"|\b(?:python|javascript|typescript|java|sql)\s+(?:code|script|program|function)\b"
        r"|\b(?:coding|programming)\b"
    ),
    "reject:homework": _rule(r"\b(?:homework|essay|assignment|thesis)\b"),
    # Markets, not money words: hikers "invest in good boots" and "stock up on water".
    "reject:finance": _rule(
        r"\b(?:stock market|stocks|crypto(?:currency)?|bitcoin|ethereum|forex|day trading"
        r"|investment advice)\b"
        r"|\binvest(?:ing)?\s+in\s+(?:stocks|crypto|bitcoin|the (?:stock )?market|real estate)\b"
    ),
    # Asking for treatment, not mentioning medicine: "bring my medication" is packing advice.
    "reject:medical": _rule(
        r"\b(?:diagnose|diagnosis|prescribe|dosage)\b"
        r"|\b(?:what|which) (?:medication|medicine|drugs?|pills?)\b"
    ),
    # "sue" needs an object, so "my friend Sue and I" is fine.
    "reject:legal": _rule(
        r"\b(?:lawsuit|lawyer|attorney|legal advice)\b"
        r"|\bsue\s+(?:the|my|them|him|her|someone|somebody|for)\b"
    ),
    # Weather only next to a "right now" word: "cold weather gear" is a hiking question.
    "reject:realtime": _rule(
        rf"\b(?:forecast|news|headlines)\b"
        rf"|\bweather\b.{{0,40}}\b{_NOW}\b|\b{_NOW}\b.{{0,40}}\bweather\b"
    ),
    "reject:harmful": _rule(
        r"\b(?:bomb|explosives?|weapons?|firearms?)\b|\bpoison\b(?!\s+(?:ivy|oak|sumac))"
    ),
}

# Shown to the user by the reject reply: "...so I can't help with <topic>."
REJECT_TOPICS: dict[str, str] = {
    "reject:code": "writing or debugging code",
    "reject:homework": "homework or essays",
    "reject:finance": "financial or investment advice",
    "reject:medical": "medical advice",
    "reject:legal": "legal advice",
    "reject:realtime": "live weather, news, or other real-time information",
    "reject:harmful": "anything that could cause harm",
}

# Hiking vocabulary. Each keyword is its own rule, so the trace shows exactly which words
# decided the route. Every keyword also matches its plural ("lake" matches "lakes"): the
# first version listed plurals by hand and missed most of them.
TRAIL_KEYWORDS = (
    "hike", "hiking", "hiker",
    "trail", "trailhead", "trek", "trekking", "backpacking",
    "summit", "peak", "ridge", "loop", "switchback", "elevation", "mile", "km",
    "waterfall", "lake", "canyon", "national park", "dog-friendly",
    "difficulty", "scenic", "campsite", "camping",
)  # fmt: skip
TRAIL_RULES: dict[str, re.Pattern[str]] = {
    f"trail:kw:{kw}": _rule(rf"\b{re.escape(kw)}s?\b") for kw in TRAIL_KEYWORDS
}

GENERAL_RULES: dict[str, re.Pattern[str]] = {
    "general:greeting": _rule(
        r"\b(?:hi|hello|hey|howdy|hiya|good (?:morning|afternoon|evening))\b"
    ),
    "general:thanks": _rule(r"\b(?:thanks|thank you|thx|cheers)\b"),
    "general:goodbye": _rule(r"\b(?:bye|goodbye|see you|see ya)\b"),
    "general:about": _rule(r"\b(?:who are you|what are you|your name)\b"),
    "general:help": _rule(r"\b(?:what can you do|help|how does this work)\b"),
    "general:smalltalk": _rule(r"\b(?:how are you|how's it going|what's up)\b"),
}

# The priority order IS the routing policy. Change it here, and only here.
_RULE_GROUPS: tuple[tuple[Category, dict[str, re.Pattern[str]]], ...] = (
    ("reject", REJECT_RULES),
    ("trail", TRAIL_RULES),
    ("general", GENERAL_RULES),
)

DEFAULT = Classification("general", ("general:default",))


def classify(text: str) -> Classification:
    """Return the first rule group (in priority order) with any matching rule."""
    for category, rules in _RULE_GROUPS:
        matched = tuple(rule_id for rule_id, pattern in rules.items() if pattern.search(text))
        if matched:
            return Classification(category, matched)
    return DEFAULT
