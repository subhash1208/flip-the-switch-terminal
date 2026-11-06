"""In-process stand-in for a Switch room. Used by `bailiff.demo --offline` and the tests.

Every participant has its own queue and sees every message (as with filter=all). Documents live in a
dict and follow the rule that creating an existing name fails. Nothing here touches a network.
The transcript is stored redacted, as Switch's guardrail stores it, and it also gets the whole-line
secret rule: a machine's JSON reply would otherwise keep the tail of a secret line. Delivered frames
stay raw, so the Bailiff's own redaction is what gets counted in the receipt.
This is NOT Switch: addressing policy is not modelled. The two document ops take the real argument
names (Switch 0.31.0 schemas) and refuse any other key with 400, as Switch does.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from bailiff.events import Event, Malformed, parse_event
from bailiff.redact import mask_bounded
from bailiff.transport import OpError

CREATE_ARGS = frozenset({"name", "description", "instructions", "content"})
UPDATE_ARGS = frozenset({"document_id", "name", "description", "instructions", "content"})


class FakeRoom:
    def __init__(self, room_id: str = "room-offline") -> None:
        self.room_id = room_id
        self.queues: dict[str, asyncio.Queue[str]] = {}
        self.messages: list[tuple[str, str]] = []
        self.documents: dict[str, str] = {}  # document_id -> content
        self.document_ids: dict[str, str] = {}  # name -> document_id
        self.ids: dict[str, str] = {}  # handle -> opaque participant id
        self._seq = 0

    def _id(self, name: str) -> str:
        return self.ids.setdefault(name, f"@switch-agent-{len(self.ids) + 1}:fake")

    def join(self, name: str) -> FakeConnection:
        self.queues[name] = asyncio.Queue()
        self._id(name)
        return FakeConnection(self, name)

    def publish(self, sender: str, text: str, display: str | None = None) -> None:
        """Post as `sender`; `display` is the free-text name a frame may claim instead."""
        self._seq += 1
        name = display or sender
        self.messages.append((name, mask_bounded(text)[0]))
        frame = json.dumps(
            {
                "event": "message",
                "id": self._seq,
                "data": {
                    "type": "message",
                    "room_id": self.room_id,
                    "payload": {
                        "sender": self._id(sender),
                        "sender_name": name,
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
        room = self._room
        if operation == "read_context":  # history holds one room_join per member, as Switch writes
            roots = [
                {"root": {"kind": "room_join", "sender": room._id(n), "sender_name": n}}
                for n in room.queues
            ]
            return {"result": {"threads": roots, "truncated": False}}
        if operation == "create_room_document":
            if set(args) != CREATE_ARGS:
                raise OpError(operation, 400, f"unexpected arguments: {sorted(args)}")
            name = str(args["name"])
            if name in room.document_ids:
                raise OpError(operation, 409, f"document {name} already exists")
            doc_id = f"doc-{len(room.documents) + 1}"
            room.document_ids[name] = doc_id
            room.documents[doc_id] = str(args["content"])
            return {"document_id": doc_id}
        if operation == "update_room_document":
            if "document_id" not in args or set(args) - UPDATE_ARGS:
                raise OpError(operation, 400, f"unexpected arguments: {sorted(args)}")
            doc_id = str(args["document_id"])
            if doc_id not in room.documents:
                raise OpError(operation, 404, f"document {doc_id} does not exist")
            if args.get("content") is not None:
                room.documents[doc_id] = str(args["content"])
            return {"document_id": doc_id}
        raise OpError(operation, 404, "fake room has no such operation")

    async def post(self, room_id: str, text: str) -> int:
        _, hits = mask_bounded(text)
        self.redactions += hits
        self._room.publish(self._name, text)
        return hits
