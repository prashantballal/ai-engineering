"""normalize_text is the first thing every message goes through (the `receive` node)."""

import pytest

from trailmate_workflow.normalize import normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  hello   world  ", "hello world"),  # collapse and trim whitespace
        ("ｈｉｋｅ", "hike"),  # full-width letters → ASCII (Unicode NFKC)
        ("ig​nore", "ignore"),  # zero-width space removed
        ("line\nbreak\ttab", "line break tab"),  # newlines and tabs become single spaces
        ("Zürich ☕", "Zürich ☕"),  # accents and emoji survive
        ("", ""),
        # Review fix: EVERY invisible character goes, not just the five zero-width ones.
        ("ig\u00adnore", "ignore"),  # soft hyphen (Unicode category Cf, "format")
        ("ig\u202enore", "ignore"),  # right-to-left override (Cf)
        ("ig\U000e0020nore", "ignore"),  # tag space (Cf)
        ("ig\u034fnore", "ignore"),  # combining grapheme joiner (invisible, but not Cf)
        ("ig\ufe0fnore", "ignore"),  # variation selector (invisible, but not Cf)
        ("You\u2019re", "You're"),  # typographic apostrophe → ' (NFKC leaves it alone)
    ],
)
def test_normalize_text(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected
