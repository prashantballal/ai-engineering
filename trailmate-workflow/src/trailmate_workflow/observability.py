"""Request logging shared by the JSON and the streaming endpoints.

Rule: log metadata only (ids, route, tier, verdicts, timings), never user or model text.
"""

import logging
import time

from trailmate_workflow.schemas import ChatResponse

logger = logging.getLogger("trailmate")


def log_request(response: ChatResponse, started: float) -> None:
    """One metadata-only log line per request."""
    logger.info(
        "request_id=%s route=%s tier=%s model=%s fallback=%s nodes=%s total_ms=%.1f",
        response.request_id,
        response.route,
        response.tier,
        response.model,
        response.fallback_used,
        ",".join(step.node for step in response.trace),
        (time.perf_counter() - started) * 1000,
    )
