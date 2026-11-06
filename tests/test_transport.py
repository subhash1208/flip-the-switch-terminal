"""SwitchConnection: pongs first, cursor resume, terminal takeover, call errors, redaction.

The WebSocket and HTTP layer are the boundary, so they are faked here. The connection logic is real.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any

import httpx
import pytest

from bailiff import transport
from bailiff.transport import (
    OpError,
    ReconnectExhausted,
    SwitchConnection,
    SwitchRefused,
    TakenOver,
)

PING = json.dumps({"event": "ping", "data": {}})
CONNECTION_STATE = json.dumps(
    {"event": "connection_state", "data": {"generation": 3, "rooms": ["r1"]}}
)


def _msg(i: int) -> str:
    return json.dumps(
        {
            "event": "message",
            "id": i,
            "data": {
                "type": "message",
                "room_id": "r1",
                "payload": {"sender": "dana", "body": f"m{i}", "message_id": f"m{i}"},
                "sequence": i,
            },
        }
    )


class FakeWS:
    """Replays frames, records what the client sends, and reports a close code."""

    def __init__(self, frames: list[str], close_code: int | None = 1000) -> None:
        self._frames = frames
        self.close_code = close_code
        self.sent: list[str] = []
        self.closed = False

    def __aiter__(self) -> AsyncIterator[str]:
        return self._replay()

    async def _replay(self) -> AsyncIterator[str]:
        for frame in self._frames:
            yield frame

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def close(self) -> None:
        self.closed = True


class FakeDial:
    """Hands out one fake socket per dial. An Exception in the list is raised instead."""

    def __init__(self, sockets: list[FakeWS | Exception]) -> None:
        self._sockets = sockets
        self.urls: list[str] = []
        self.headers: list[dict[str, str]] = []

    async def __call__(self, url: str, headers: dict[str, str]) -> FakeWS:
        self.urls.append(url)
        self.headers.append(headers)
        nxt = self._sockets.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def _conn(
    dial: FakeDial, transport: httpx.AsyncBaseTransport | None = None, **kwargs: Any
) -> SwitchConnection:
    return SwitchConnection(
        "http://switch.test",
        "agent-1",
        "secret-key",
        "conn-1",
        ["r1"],
        backoff=0,
        dial=dial,
        transport=transport,
        **kwargs,
    )


@pytest.mark.asyncio
async def test_the_default_dial_pins_the_one_mib_frame_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    async def connect(url: str, **kwargs: Any) -> str:
        seen["url"] = url
        seen.update(kwargs)
        return "socket"

    monkeypatch.setattr(transport.websockets, "connect", connect)
    assert await transport._default_dial("ws://h/x", {"A": "1"}) == "socket"
    assert seen == {
        "url": "ws://h/x",
        "additional_headers": {"A": "1"},
        "max_size": 2**20,
    }


@pytest.mark.asyncio
async def test_ping_is_answered_with_a_pong_carrying_the_cursor_before_the_next_event() -> None:
    ws = FakeWS([CONNECTION_STATE, _msg(5), PING, _msg(6)])
    conn = _conn(FakeDial([ws]))
    sent_when_six_arrived: list[str] = []
    async with conn, aclosing(conn.events()) as stream:
        async for ev in stream:
            if ev.cursor == 6:
                sent_when_six_arrived = list(ws.sent)
                break
    assert [json.loads(s) for s in sent_when_six_arrived] == [{"type": "pong", "cursor": 5}]


@pytest.mark.asyncio
async def test_reconnect_resumes_from_the_last_cursor_and_generation() -> None:
    first = FakeWS([CONNECTION_STATE, _msg(5)], close_code=1012)
    second = FakeWS([_msg(6)])
    dial = FakeDial([first, second])
    conn = _conn(dial)
    cursors: list[int | None] = []
    async with conn, aclosing(conn.events()) as stream:
        async for ev in stream:
            cursors.append(ev.cursor)
            if len(cursors) == 3:
                break
    assert cursors == [None, 5, 6]
    assert "start_from" not in dial.urls[0]
    assert "start_from=5" in dial.urls[1] and "expected_generation=3" in dial.urls[1]
    assert dial.headers[0] == {"Authorization": "Bearer secret-key"}


@pytest.mark.asyncio
async def test_taken_over_is_terminal_and_never_redials() -> None:
    evicted = json.dumps({"event": "evicted", "data": {"code": "taken_over", "reason": "replaced"}})
    dial = FakeDial([FakeWS([evicted])])
    conn = _conn(dial)
    async with conn, aclosing(conn.events()) as stream:
        with pytest.raises(TakenOver):
            async for _ in stream:
                pass
    assert len(dial.urls) == 1


@pytest.mark.asyncio
async def test_refused_close_code_is_not_retried() -> None:
    dial = FakeDial([FakeWS([], close_code=4401)])
    conn = _conn(dial)
    async with conn, aclosing(conn.events()) as stream:
        with pytest.raises(SwitchRefused):
            async for _ in stream:
                pass
    assert len(dial.urls) == 1


@pytest.mark.asyncio
async def test_reconnect_cap_gives_up_with_a_clear_error() -> None:
    dial = FakeDial([OSError("connection refused")] * 5)
    conn = _conn(dial, max_reconnects=2)
    async with conn, aclosing(conn.events()) as stream:
        with pytest.raises(ReconnectExhausted, match="2 reconnect attempts"):
            async for _ in stream:
                pass
    assert len(dial.urls) == 3


@pytest.mark.asyncio
async def test_non_2xx_call_raises_op_error_and_sends_the_bearer_key() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        seen["connection"] = request.headers["X-Switch-Connection-Id"]
        return httpx.Response(409, json={"error": "stale"})

    async with _conn(FakeDial([]), transport=httpx.MockTransport(handler)) as conn:
        with pytest.raises(OpError) as err:
            await conn.op(
                "create_room_document",
                name="case-1",
                description="d",
                instructions="i",
                content="x",
            )
    assert err.value.status == 409
    assert seen == {"auth": "Bearer secret-key", "connection": "conn-1"}


@pytest.mark.asyncio
async def test_outbound_text_is_redacted_counted_and_sent_to_the_message_route() -> None:
    sent: list[tuple[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append((request.url.path, json.loads(request.content)))
        return httpx.Response(200, json={"ok": True})

    async with _conn(FakeDial([]), transport=httpx.MockTransport(handler)) as conn:
        hits = await conn.post("r1", "env dump: DATABASE_PASSWORD=hunter2 end")
        assert conn.redactions == hits
    assert hits >= 1
    assert "hunter2" not in json.dumps(sent)
    assert sent[0][0] == "/agents/agent-1/message"
    assert sent[0][1]["room_id"] == "r1"


@pytest.mark.asyncio
async def test_post_sends_the_redacted_content_and_counts_it() -> None:
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True})

    async with _conn(FakeDial([]), transport=httpx.MockTransport(handler)) as conn:
        hits = await conn.post("r1", "x?a=1&token=abc123")
    assert hits == 1
    assert sent == [{"room_id": "r1", "content": "x?a=1&token=[redacted]"}]


@pytest.mark.asyncio
async def test_an_oversized_post_is_capped_and_says_so() -> None:
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True})

    async with _conn(FakeDial([]), transport=httpx.MockTransport(handler)) as conn:
        await conn.post("r1", "x " * 40_000)
    content: str = sent[0]["content"]
    assert len(content) < 65_536 + 40
    assert "[truncated " in content and content.endswith(" chars]")


@pytest.mark.asyncio
async def test_socket_is_closed_when_the_stream_ends_in_error() -> None:
    evicted = json.dumps({"event": "evicted", "data": {"code": "taken_over", "reason": "replaced"}})
    ws = FakeWS([evicted])
    conn = _conn(FakeDial([ws]))
    async with conn, aclosing(conn.events()) as stream:
        with pytest.raises(TakenOver):
            async for _ in stream:
                pass
    assert ws.closed is True


@pytest.mark.asyncio
async def test_http_client_is_closed_when_the_caller_fails_inside_the_block() -> None:
    conn = _conn(FakeDial([]), transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    with pytest.raises(RuntimeError, match="boom"):
        async with conn:
            raise RuntimeError("boom")
    assert conn._http.is_closed is True


@pytest.mark.asyncio
async def test_one_frame_then_a_drop_each_time_still_hits_the_reconnect_cap() -> None:
    dial = FakeDial([FakeWS([_msg(i)], close_code=1012) for i in range(1, 6)])
    conn = _conn(dial, max_reconnects=2, clock=lambda: 0.0)
    async with conn, aclosing(conn.events()) as stream:
        with pytest.raises(ReconnectExhausted, match="2 reconnect attempts"):
            async for _ in stream:
                pass
    assert len(dial.urls) == 3


@pytest.mark.asyncio
async def test_a_connection_that_stayed_up_long_enough_resets_the_reconnect_cap() -> None:
    ticks = itertools.count(0, 11)  # every clock read is 11s later, so each socket looks stable
    dial = FakeDial([FakeWS([_msg(i)], close_code=1012) for i in range(1, 6)])
    conn = _conn(dial, max_reconnects=1, clock=lambda: float(next(ticks)))
    cursors: list[int | None] = []
    async with conn, aclosing(conn.events()) as stream:
        async for ev in stream:
            cursors.append(ev.cursor)
            if len(cursors) == 4:
                break
    assert cursors == [1, 2, 3, 4]


def _gap(resumed_at: int) -> str:
    data = {"from_sequence": 2, "resumed_at": resumed_at, "rooms": ["r1"], "reason": "window"}
    return json.dumps({"event": "gap", "data": data})


@pytest.mark.asyncio
async def test_gap_moves_the_cursor_to_resumed_at_even_backwards_and_is_counted() -> None:
    conn = _conn(FakeDial([FakeWS([_msg(12), _gap(5), _gap(20)])]))
    cursors: list[int | None] = []
    async with conn, aclosing(conn.events()) as stream:
        async for _ in stream:
            cursors.append(conn.cursor)
            if len(cursors) == 3:
                break
    assert cursors == [12, 5, 20]
    assert conn.gaps == 2


@pytest.mark.asyncio
async def test_closed_eviction_is_terminal_and_carries_the_reason() -> None:
    data = {"code": "closed", "reason": "agent deleted"}
    evicted = json.dumps({"event": "evicted", "data": data})
    dial = FakeDial([FakeWS([evicted])])
    conn = _conn(dial)
    async with conn, aclosing(conn.events()) as stream:
        with pytest.raises(SwitchRefused, match="agent deleted"):
            async for _ in stream:
                pass
    assert len(dial.urls) == 1


def test_an_empty_rooms_list_fails_loudly_before_any_connection() -> None:
    with pytest.raises(ValueError, match="at least one room"):
        SwitchConnection("http://switch.test", "agent-1", "secret-key", "conn-1", [])
