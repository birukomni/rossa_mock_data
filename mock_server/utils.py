"""Shared utilities."""
from __future__ import annotations
import asyncio
import os
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


async def maybe_delay() -> None:
    ms = int(os.getenv("MOCK_DELAY_MS", "0"))
    if ms > 0:
        await asyncio.sleep(ms / 1000)
