"""Text normalization: the step every later rule depends on.

Rules and guardrails match on text, and the same visible text can be written in many
ways: full-width letters (ｉｇｎｏｒｅ), invisible characters inside a word ("ig", U+200B,
"nore"), typographic apostrophes (you’re), tabs and newlines. Normalizing once, up front,
means every later rule sees one canonical form. Without it, a guardrail looking for
"ignore" never sees one written with hidden characters.
"""

import unicodedata

# Characters that render as nothing, so they can hide inside a word. Unicode files most of
# them under the "format" category, Cf: zero-width spaces and joiners, the soft hyphen,
# left-to-right and right-to-left marks, tag characters, and more. A short list would
# miss some (the first version listed five and missed all of those). Two invisible kinds
# sit outside Cf, so they're listed by code point: the combining grapheme joiner and the
# variation selectors.
_INVISIBLE_OUTSIDE_CF = ((0x034F, 0x034F), (0xFE00, 0xFE0F), (0xE0100, 0xE01EF))

# NFKC leaves typographic apostrophes alone, and phones and Macs type ’ by default.
_APOSTROPHES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u02bc": "'"})


def is_invisible(char: str) -> bool:
    """True for a character that shows nothing on screen."""
    if unicodedata.category(char) == "Cf":
        return True
    return any(low <= ord(char) <= high for low, high in _INVISIBLE_OUTSIDE_CF)


def normalize_text(text: str) -> str:
    """NFKC-normalize, drop invisible characters, straighten apostrophes, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text).translate(_APOSTROPHES)
    text = "".join(char for char in text if not is_invisible(char))
    return " ".join(text.split())
