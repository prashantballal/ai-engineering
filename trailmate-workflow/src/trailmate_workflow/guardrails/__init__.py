"""Rule-based guardrails: input checks, output checks, and the in-stream guard.

These are plain functions with no LangGraph imports, so they're easy to test in isolation.
The graph nodes that call them live in graph/guardrail_nodes.py.
"""
