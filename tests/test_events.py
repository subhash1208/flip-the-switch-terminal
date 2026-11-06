"""parse_event never raises; good frames map to Event, bad ones to Malformed."""

from __future__ import annotations

import json

import pytest

from bailiff.events import MAX_FRAME_CHARS, RES, Event, Malformed, parse_event, read_wire

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
                "payload": {
                    "sender": "@switch-user-1:x",
                    "sender_name": "Dana",
                    "body": "!open case x",
                    "message_id": "m7",
                },
                "sequence": 7,
            },
        }
    )
    ev = parse_event(raw)
    assert isinstance(ev, Event)
    assert (ev.type, ev.room_id, ev.sender, ev.sender_name, ev.text, ev.cursor) == (
        "message",
        "r1",
        "@switch-user-1:x",
        "Dana",
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


def _res(**fields: object) -> str:
    return json.dumps({"request_id": "r1", "machine": "alice", "exit_code": 0, **fields})


@pytest.mark.parametrize(
    "text",
    [
        f"BAILIFF-RES ```json\n{_res()}\n```",
        f"BAILIFF-RES   {_res()}",
        f" BAILIFF-RES {_res()}",
        f"Done, here it is. BAILIFF-RES {_res()} Thanks!",
        f"I will answer with BAILIFF-RES once ready. BAILIFF-RES {_res()}",
        f'BAILIFF-RES {{"note": 1}} BAILIFF-RES {_res()}',
    ],
)
def test_read_wire_finds_the_reply_through_fences_spaces_and_chatter(text: str) -> None:
    assert read_wire(text, RES) == json.loads(_res())


@pytest.mark.parametrize(
    "text",
    [
        None,
        "no marker here",
        f"BAILIFF-REQ {_res()}",
        "BAILIFF-RES [1, 2]",
        'BAILIFF-RES {"request_id": ',
        'BAILIFF-RES {"exit_code": 0}',
        "BAILIFF-RES {" + '"a":' + "[" * 100_000,
        f"BAILIFF-RES {'{x} ' * 60}{_res()}",
        "BAILIFF-RES " + _res() + " " * MAX_FRAME_CHARS,
    ],
)
def test_read_wire_rejects_what_is_not_a_reply(text: str | None) -> None:
    assert read_wire(text, RES) is None


def test_read_wire_skips_a_quoted_request_and_takes_the_reply_that_has_an_exit_code() -> None:
    request = '{"request_id": "r1", "machine": "bob", "kind": "probe", "argv": ["uname"]}'
    reply = '{"request_id": "r1", "machine": "bob", "exit_code": 0}'
    text = f"BAILIFF-RES for BAILIFF-REQ {request} then BAILIFF-RES {reply}"
    assert read_wire(text, RES, ("request_id", "exit_code")) == json.loads(reply)
