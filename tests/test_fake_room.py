"""The fake post counts masking over the bounded text, as the real post does."""

from __future__ import annotations

import pytest

from bailiff.redact import MAX_REDACT_CHARS
from bailiff.scripted.fake_room import FakeRoom
from bailiff.transport import OpError


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


CREATE = {"name": "case-1", "description": "d", "instructions": "i", "content": "v1"}


@pytest.mark.asyncio
async def test_create_takes_the_real_arguments_and_returns_a_document_id() -> None:
    room = FakeRoom()
    reply = await room.join("bailiff").op("create_room_document", **CREATE)
    assert reply == {"document_id": "doc-1"}
    assert room.documents == {"doc-1": "v1"}


@pytest.mark.asyncio
async def test_update_replaces_content_by_document_id() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    doc_id = (await conn.op("create_room_document", **CREATE))["document_id"]
    await conn.op("update_room_document", document_id=doc_id, content="v2")
    assert room.documents == {doc_id: "v2"}


@pytest.mark.asyncio
async def test_old_argument_shapes_are_refused_with_400() -> None:
    conn = FakeRoom().join("bailiff")
    with pytest.raises(OpError) as create:
        await conn.op("create_room_document", name="case-1", content="v1")
    assert create.value.status == 400
    with pytest.raises(OpError) as update:
        await conn.op("update_room_document", name="case-1", content="v2")
    assert update.value.status == 400


@pytest.mark.asyncio
async def test_update_of_an_unknown_document_id_is_404() -> None:
    conn = FakeRoom().join("bailiff")
    with pytest.raises(OpError) as err:
        await conn.op("update_room_document", document_id="doc-9", content="v2")
    assert err.value.status == 404
