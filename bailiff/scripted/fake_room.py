"""In-process stand-in for a Switch room. Used by `bailiff.demo --offline` and the tests.

Every participant has its own queue and sees every message (as with filter=all). Documents live in a
dict and follow the rule that creating an existing name fails. Nothing here touches a network.
The transcript is stored redacted, as Switch's guardrail stores it, and it also gets the whole-line
secret rule: a machine's JSON reply would otherwise keep the tail of a secret line. Delivered frames
stay raw, so the Bailiff's own redaction is what gets counted in the receipt.
This is NOT Switch: addressing policy and the real operation argument schemas are not modelled.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from bailiff.events import Event, Malformed, parse_event
from bailiff.redact import mask_bounded
from bailiff.transport import OpError


class FakeRoom:
    def __init__(self, room_id: str = "room-offline") -> None:
        self.room_id = room_id
        self.queues: dict[str, asyncio.Queue[str]] = {}
        self.messages: list[tuple[str, str]] = []
        self.documents: dict[str, str] = {}
        self._seq = 0

    def join(self, name: str) -> FakeConnection:
        self.queues[name] = asyncio.Queue()
        return FakeConnection(self, name)

    def publish(self, sender: str, text: str) -> None:
        self._seq += 1
        self.messages.append((sender, mask_bounded(text)[0]))
        frame = json.dumps(
            {
                "event": "message",
                "id": self._seq,
                "data": {
                    "type": "message",
                    "room_id": self.room_id,
                    "payload": {
                        "sender": sender,
                        "body": text,
                        "message_id": f"m{self._seq}",
                        "addressed": True,
                    },
                    "sequence": self._seq,
                },
            }
        )
        for queue in self.queues.values():
            queue.put_nowait(frame)

    def push_raw(self, name: str, raw: str) -> None:
        self.queues[name].put_nowait(raw)


class FakeConnection:
    def __init__(self, room: FakeRoom, name: str) -> None:
        self._room = room
        self._name = name
        self.malformed = 0
        self.redactions = 0

    async def events(self) -> AsyncIterator[Event]:
        queue = self._room.queues[self._name]
        while True:
            frame = parse_event(await queue.get())
            if isinstance(frame, Malformed):
                self.malformed += 1
                continue
            yield frame

    async def op(self, operation: str, /, **args: Any) -> dict[str, Any]:
        if operation not in ("create_room_document", "update_room_document"):
            raise OpError(operation, 404, "fake room has no such operation")
        doc = str(args["name"])
        if operation == "create_room_document" and doc in self._room.documents:
            raise OpError(operation, 409, f"document {doc} already exists")
        if operation == "update_room_document" and doc not in self._room.documents:
            raise OpError(operation, 404, f"document {doc} does not exist")
        self._room.documents[doc] = str(args["content"])
        return {"result": {"name": doc}}

    async def post(self, room_id: str, text: str) -> int:
        _, hits = mask_bounded(text)
        self.redactions += hits
        self._room.publish(self._name, text)
        return hits
