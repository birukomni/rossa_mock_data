"""
Shared utility helpers for resolvers.
"""
from __future__ import annotations
import asyncio
import random
from datetime import datetime, timezone


def utc_now() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def maybe_delay(min_ms: int = 0, max_ms: int = 50) -> None:
    """Optional artificial latency to simulate network round-trips."""
    if max_ms > 0:
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)
