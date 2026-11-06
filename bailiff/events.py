"""Parse Switch agent-protocol frames. `parse_event` never raises."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

MAX_FRAME_CHARS = 256 * 1024
REQ = "BAILIFF-REQ"
RES = "BAILIFF-RES"


@dataclass(frozen=True)
class Event:
    type: str
    room_id: str | None
    sender: str | None
    text: str | None
    raw: str
    cursor: int | None


@dataclass(frozen=True)
class Malformed:
    reason: str
    preview: str


def _str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def parse_event(raw: str | bytes) -> Event | Malformed:
    """Parse one WebSocket frame. Bad input becomes Malformed; this never raises."""
    try:
        return _parse(raw)
    except Exception as exc:  # the contract is "never raises"; this is the last line of defence
        return Malformed(f"internal error: {type(exc).__name__}", "")


def _parse(raw: str | bytes) -> Event | Malformed:
    if len(raw) > MAX_FRAME_CHARS:
        return Malformed("frame too large", "")
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return Malformed("not utf-8", "")
    else:
        text = raw
    preview = text[:120]
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return Malformed("bad json", preview)
    if not isinstance(obj, dict):
        return Malformed("frame is not an object", preview)
    frame_type = _str(obj.get("event")) or _str(obj.get("type"))
    if frame_type is None:
        return Malformed("no frame type", preview)
    data = obj.get("data", {})
    if not isinstance(data, dict):
        return Malformed("data is not an object", preview)
    sender: str | None = None
    body: str | None = None
    if frame_type == "message":
        payload = data.get("payload")
        if not isinstance(payload, dict):
            return Malformed("message without payload", preview)
        sender = _str(payload.get("sender"))
        body = _str(payload.get("body"))
        if sender is None or body is None:
            return Malformed("message missing sender or body", preview)
    cursor = _int(obj.get("id"))
    if cursor is None:
        cursor = _int(data.get("sequence"))
    return Event(frame_type, _str(data.get("room_id")), sender, body, text, cursor)


def detail(ev: Event) -> dict[str, Any]:
    """The `data` object of a frame, re-read from its raw text. Empty when absent."""
    data = json.loads(ev.raw).get("data")
    return data if isinstance(data, dict) else {}


def message_id(ev: Event) -> str | None:
    payload = detail(ev).get("payload")
    return _str(payload.get("message_id")) if isinstance(payload, dict) else None


def read_wire(text: str | None, marker: str) -> dict[str, Any] | None:
    """The JSON object that follows `marker ` in a room message, or None."""
    if text is None:
        return None
    start = text.find(marker + " ")
    if start < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start + len(marker) + 1)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None
