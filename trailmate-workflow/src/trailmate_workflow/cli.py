"""The `trailmate` command-line tool.

uv run trailmate graph                          # print the workflow as a Mermaid diagram
uv run trailmate chat "easy hike near a lake?"  # stream a reply, showing every step
uv run trailmate chat --raw "hello"             # show the raw SSE wire format instead
"""

import argparse
import sys
from typing import Any, TextIO

import httpx

from trailmate_workflow.config import get_settings
from trailmate_workflow.graph.builder import build_graph
from trailmate_workflow.llm import make_reply_models
from trailmate_workflow.sse import SSEEvent, parse_sse

DEFAULT_URL = "http://127.0.0.1:8000"


def _details(details: dict[str, Any]) -> str:
    """Compact `key=value` rendering of a step's metadata."""
    parts = []
    for key, value in details.items():
        if isinstance(value, list):
            value = ",".join(map(str, value)) or "-"
        parts.append(f"{key}={value}")
    return " ".join(parts)


class EventPrinter:
    """Prints SSE events for a human: steps on their own lines, reply tokens inline."""

    def __init__(self, out: TextIO) -> None:
        self.out = out
        self.in_reply = False  # are we partway through a line of reply text?

    def _line(self, text: str) -> None:
        if self.in_reply:  # finish the reply line before printing anything else
            self.out.write("\n")
            self.in_reply = False
        self.out.write(text + "\n")
        self.out.flush()

    def __call__(self, event: SSEEvent) -> None:
        data = event.data
        if event.event == "start":
            self._line(f"→ request {data['request_id']}")
        elif event.event == "step":
            info = _details(data.get("details", {}))
            self._line(
                f"✓ {data['node']:<16} {data['outcome']:<10} {info}  ({data['duration_ms']} ms)"
            )
        elif event.event == "token":
            if not self.in_reply:
                self.out.write("  │ ")
                self.in_reply = True
            self.out.write(data["text"])  # inline, exactly as it arrives
            self.out.flush()
        elif event.event == "retract":
            self._line(f"⟲ replaced ({data['reason']}): {data['replacement']}")
        elif event.event == "done":
            self._line(
                f"── route={data.get('route')} tier={data.get('tier')} model={data.get('model')} "
                f"fallback={data.get('fallback_used')} blocked={data.get('blocked', False)}"
            )
        elif event.event == "error":
            self._line(f"✗ {data['message']}")


def chat(message: str, url: str, raw: bool, out: TextIO) -> int:
    """POST the message to /chat/stream and print events as they arrive."""
    printer = EventPrinter(out)
    timeout = httpx.Timeout(10.0, read=None)  # replies stream for a while; pings keep it alive
    try:
        with httpx.stream(
            "POST", f"{url}/chat/stream", json={"message": message}, timeout=timeout
        ) as response:
            if response.status_code != 200:
                out.write(f"✗ HTTP {response.status_code}: {response.read().decode()[:300]}\n")
                return 1
            if raw:
                for line in response.iter_lines():
                    out.write(line + "\n")
                    out.flush()
                return 0
            finished = False
            for event in parse_sse(response.iter_lines()):
                printer(event)
                finished = finished or event.event == "done"
            return 0 if finished else 1
    except httpx.ConnectError:
        out.write(
            f"✗ API not reachable at {url}. Start it with: "
            "uv run uvicorn trailmate_workflow.api:app --host 127.0.0.1 --port 8000\n"
        )
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trailmate", description="TrailMate workflow tools")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("graph", help="print the workflow graph as Mermaid text")
    chat_cmd = commands.add_parser("chat", help="send a message and watch the streamed reply")
    chat_cmd.add_argument("message")
    chat_cmd.add_argument(
        "--url", default=DEFAULT_URL, help=f"API base URL (default {DEFAULT_URL})"
    )
    chat_cmd.add_argument("--raw", action="store_true", help="print the raw SSE lines")

    args = parser.parse_args(argv)
    if args.command == "graph":
        # draw_mermaid() is pure text, computed locally. (draw_mermaid_png() would call an
        # external web API, so it's deliberately not used.)
        settings = get_settings()
        graph = build_graph(make_reply_models(settings), settings)  # no network call
        print(graph.get_graph().draw_mermaid())
        return 0
    return chat(args.message, args.url, args.raw, sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
