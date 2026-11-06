"""parse_event never raises; good frames map to Event, bad ones to Malformed."""

from __future__ import annotations

import json

from bailiff.events import Event, Malformed, parse_event

WEIRD: list[str | bytes] = [
    "",
    "{",
    "[]",
    "null",
    "42",
    '"just a string"',
    "{}",
    '{"event": "message"}',
    '{"event": "message", "data": {}}',
    '{"event": "message", "data": {"payload": "x"}}',
    '{"event": "message", "data": {"payload": {"sender": 1, "body": "x"}}}',
    '{"event": "message", "data": {"payload": {"sender": "a", "body": null}}}',
    '{"event": null}',
    '{"event": "ping", "data": []}',
    '{"event": "ping", "id": true}',
    '{"event": "ping", "id": 1e999}',
    '{"event": "ping", "data": {"sequence": "9"}}',
    b"\xff\xfe\x00",
    b"",
    "NaN",
    '{"event": "message", "data": {"payload": {"sender": "a", "body": "' + "x" * 300_000 + '"}}}',
    '{"event": "x"',
]


def test_parse_event_never_raises_on_hostile_input() -> None:
    assert len(WEIRD) >= 20
    for raw in WEIRD:
        assert isinstance(parse_event(raw), (Event, Malformed))


def test_message_frame_maps_to_event_fields() -> None:
    raw = json.dumps(
        {
            "event": "message",
            "id": 7,
            "data": {
                "type": "message",
                "room_id": "r1",
                "payload": {"sender": "dana", "body": "!open case x", "message_id": "m7"},
                "sequence": 7,
            },
        }
    )
    ev = parse_event(raw)
    assert isinstance(ev, Event)
    assert (ev.type, ev.room_id, ev.sender, ev.text, ev.cursor) == (
        "message",
        "r1",
        "dana",
        "!open case x",
        7,
    )


def test_unknown_frame_type_is_kept_as_an_event_not_rejected() -> None:
    ev = parse_event('{"event": "gap", "data": {"resumed_at": 9}}')
    assert isinstance(ev, Event)
    assert ev.type == "gap"
    assert ev.text is None and ev.cursor is None


def test_message_with_wrong_field_types_is_malformed_with_a_reason() -> None:
    result = parse_event(
        json.dumps({"event": "message", "data": {"payload": {"sender": 1, "body": "x"}}})
    )
    assert isinstance(result, Malformed)
    assert "missing" in result.reason
