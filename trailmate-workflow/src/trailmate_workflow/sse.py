"""A minimal Server-Sent Events parser (client side), following the WHATWG rules we need.

The wire format is plain text. Each event is a few `field: value` lines followed by a
blank line:

    event: token
    data: {"text": "Try "}
    <blank line>          ← dispatches the event

Lines starting with ':' are comments; servers send them as keep-alive pings. Several
`data:` lines in one event are joined with "\\n". An event cut off before its blank line
is never dispatched.
"""

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SSEEvent:
    event: str
    data: dict[str, Any]


def parse_sse(lines: Iterable[str]) -> Iterator[SSEEvent]:
    """Turn lines of an SSE stream into events whose `data` is decoded JSON."""
    event, data_lines = "message", []
    for line in lines:
        if line == "":  # blank line: dispatch the event built so far
            if data_lines:
                yield SSEEvent(event, json.loads("\n".join(data_lines)))
            event, data_lines = "message", []
        elif line.startswith(":"):  # comment, e.g. a keep-alive ping
            continue
        else:
            field, _, value = line.partition(":")
            value = value.removeprefix(" ")  # one optional space after the colon
            if field == "event":
                event = value
            elif field == "data":
                data_lines.append(value)
            # `id:` and `retry:` matter for auto-reconnecting clients; ignored here.
