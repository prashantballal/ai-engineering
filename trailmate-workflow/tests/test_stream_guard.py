"""Day 5: StreamGuard, which checks model output WHILE it streams.

The hard case is a pattern split across chunks: "jane." + "doe@exa" + "mple.com". The
guard must never release any part of it unredacted, whatever the chunk boundaries.
"""

import random
import time

import pytest
from fake_pii import FAKE_CARD_SPACED, FAKE_EMAIL, FAKE_PHONE_SPACED

from trailmate_workflow.guardrails.output_checks import check_output
from trailmate_workflow.guardrails.stream_guard import StreamGuard
from trailmate_workflow.prompts import CANARY

FILLER = " More trail words follow here." * 4


def run(text: str, size: int, holdback: int = 48) -> tuple[str, StreamGuard]:
    """Feed `text` in `size`-character chunks; return everything released plus the guard."""
    guard = StreamGuard(CANARY, holdback=holdback)
    out = "".join(guard.feed(text[i : i + size]) for i in range(0, len(text), size))
    return out + guard.flush(), guard


@pytest.mark.parametrize(
    "secret", [FAKE_EMAIL, FAKE_PHONE_SPACED, FAKE_CARD_SPACED, "https://trails.example.org/mist"]
)
@pytest.mark.parametrize("size", [1, 3, 7])
def test_pattern_split_across_chunks_never_leaks(secret: str, size: int) -> None:
    out, _ = run(f"Write to {secret} for maps.{FILLER}", size)

    assert secret not in out
    assert secret[:6] not in out  # not even a fragment


def test_plain_text_is_released_with_bounded_lag() -> None:
    guard = StreamGuard(CANARY, holdback=48)
    text = "word " * 60
    released = "".join(guard.feed(text[i : i + 5]) for i in range(0, len(text), 5))

    assert len(text) - len(released) <= 48 + 5  # lag: at most the holdback plus one word
    assert released + guard.flush() == text  # and nothing is lost at the end


def test_canary_stops_release() -> None:
    out, guard = run(f"Here is a note {CANARY} and more text after it.{FILLER}", 4)

    assert guard.blocked and guard.block_reason == "canary_leak"
    assert CANARY not in out
    assert "more text after it" not in out  # nothing after the leak is released


@pytest.mark.parametrize(
    "text", [f"Mail {FAKE_EMAIL} now.{FILLER}", f"See www.example.org today.{FILLER}"]
)
def test_stream_output_matches_the_full_reply_check(text: str) -> None:
    out, _ = run(text, 3)

    assert out == check_output(text, CANARY).text


def test_raw_and_released_text_are_tracked() -> None:
    out, guard = run(f"Mail {FAKE_EMAIL} now.{FILLER}", 5)

    assert guard.raw_text == f"Mail {FAKE_EMAIL} now.{FILLER}"
    assert guard.released_text == out


@pytest.mark.parametrize("size", [1, 3, 7])
def test_card_next_to_other_digits_never_leaks(size: int) -> None:
    # Review fix: a card followed by an expiry date and a CVV, split at every chunk size.
    out, _ = run(f"Card {FAKE_CARD_SPACED} 12/26 123 is on file.{FILLER}", size)

    assert "[CARD] 12/26 123" in out
    assert FAKE_CARD_SPACED[:6] not in out


def test_abuse_word_cut_by_a_chunk_boundary_is_not_blocked() -> None:
    # Review fix: "idiot" + "ically" is "idiotically", not an insult. A tokenizer can split
    # it right there, and the end of the text so far looks like the end of a word.
    guard = StreamGuard(CANARY, holdback=48)
    chunks = ["The climb was idiot", "ically steep, so pick the easier lakeside loop today."]

    out = "".join(guard.feed(chunk) for chunk in chunks) + guard.flush()

    assert not guard.blocked
    assert out == "".join(chunks)


def test_abuse_word_at_the_very_end_is_still_blocked() -> None:
    out, guard = run("That was a great hike, you idiot", 4)

    assert guard.blocked and guard.block_reason == "abusive_language"
    assert "idiot" not in out


SAMPLES = [
    f"Mail {FAKE_EMAIL} or call {FAKE_PHONE_SPACED} about the permit.{FILLER}",
    f"Card {FAKE_CARD_SPACED} 12/26 123 is on file; see www.example.org today.{FILLER}",
    f"The climb was idiotically steep near the lake.{FILLER}",
    # A link that ends in a digit, right before a card: the digit run starts INSIDE the
    # link, so moving the cut back to the run's start lands it inside the link.
    f"Map: https://x.example.org/a?b=1 {FAKE_CARD_SPACED} for the loop.{FILLER}",
]


@pytest.mark.parametrize("text", SAMPLES)
def test_any_chunking_shows_what_the_full_reply_check_shows(text: str) -> None:
    # A property test: however the reply is cut into chunks (200 seeded random cuttings),
    # the stream shows exactly what check_output shows for the whole reply.
    rng = random.Random(7)
    for _ in range(200):
        guard, out, i = StreamGuard(CANARY, holdback=48), "", 0
        while i < len(text):
            size = rng.randint(1, 12)
            out += guard.feed(text[i : i + size])
            i += size
        out += guard.flush()

        assert not guard.blocked
        assert out == check_output(text, CANARY).text


@pytest.mark.parametrize("text", ["a" * 6000, "Take the lakeside loop to the ridge. " * 160])
def test_long_replies_stay_fast(text: str) -> None:
    # Review fix: the guard rescanned the WHOLE reply on every chunk. 6,000 characters with
    # no spaces took over 10 seconds, and since the guard runs on the event loop, every
    # other request waited too. Now each chunk costs about the same, however long the reply.
    started = time.perf_counter()

    run(text, 4)

    assert time.perf_counter() - started < 0.25
