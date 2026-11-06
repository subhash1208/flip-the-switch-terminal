"""The fake post counts masking over the bounded text, as the real post does."""

from __future__ import annotations

import pytest

from bailiff.redact import MAX_REDACT_CHARS
from bailiff.scripted.fake_room import FakeRoom


@pytest.mark.asyncio
async def test_a_secret_past_the_bound_is_neither_counted_nor_published() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    hits = await conn.post("room-offline", "x" * MAX_REDACT_CHARS + " DATABASE_PASSWORD=hunter2")
    assert hits == 0
    assert conn.redactions == 0
    _, posted = room.messages[-1]
    assert "hunter2" not in posted
    assert "[truncated" in posted


@pytest.mark.asyncio
async def test_a_secret_inside_the_bound_is_counted_and_masked() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    hits = await conn.post("room-offline", "DATABASE_PASSWORD=hunter2")
    assert hits == 1
    assert conn.redactions == 1
    _, posted = room.messages[-1]
    assert "hunter2" not in posted
