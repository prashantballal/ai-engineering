"""pytest fixtures shared by every test module."""

from collections.abc import AsyncIterator

import httpx
import pytest
from helpers import client_for, graph_with


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """An HTTP client for an app running the real graph with scripted fake models."""
    async with client_for(graph_with()) as c:
        yield c
