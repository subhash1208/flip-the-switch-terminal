"""Live mode unit tests: registration, reply parsing and the observer. No network."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from bailiff import live
from bailiff.live import LiveError, _register, _Tap, room_id_from
from bailiff.scripted.fake_room import FakeRoom
from bailiff.transport import ReconnectExhausted, SwitchConnection


def _client(handler: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url="http://switch.test",
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer bootstrap-token"},
    )


def test_register_returns_the_id_and_key_the_server_issued() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer bootstrap-token"
        return httpx.Response(200, json={"id": "agent-1", "api_key": "key-1"})

    async def run() -> tuple[str, str]:
        async with _client(handler) as http:
            return await _register(http, "bailiff")

    assert asyncio.run(run()) == ("agent-1", "key-1")


def test_register_on_409_retries_once_with_overwrite_to_rotate_the_key() -> None:
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        sent.append(body)
        if body.get("overwrite"):
            return httpx.Response(200, json={"id": "agent-2", "api_key": "key-2"})
        return httpx.Response(409, json={"detail": "already registered"})

    async def run() -> tuple[str, str]:
        async with _client(handler) as http:
            return await _register(http, "bob-codex")

    assert asyncio.run(run()) == ("agent-2", "key-2")
    assert [body.get("overwrite") for body in sent] == [None, True]
    assert sent[0]["name"] == "bob-codex"


def test_register_refusal_names_the_agent_status_and_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="bad registration token")

    async def run() -> None:
        async with _client(handler) as http:
            await _register(http, "bailiff")

    with pytest.raises(LiveError, match=r"register bailiff failed with HTTP 401: bad registration"):
        asyncio.run(run())


@pytest.mark.parametrize("reply", [{}, {"result": {}}, {"result": "room-1"}])
def test_create_room_reply_without_an_id_is_a_live_error(reply: dict[str, Any]) -> None:
    with pytest.raises(LiveError, match="no room id"):
        room_id_from(reply)


def test_create_room_reply_yields_the_room_id_from_result() -> None:
    reply = {"result": {"id": "ff4c0736", "name": "x", "failed_attachments": []}}
    assert room_id_from(reply) == "ff4c0736"


class _FakeWs:
    """A WebSocket that yields canned frames, then ends so the connection drops."""

    close_code = 1000

    def __init__(self, frames: list[str]) -> None:
        self._frames = iter(frames)

    def __aiter__(self) -> _FakeWs:
        return self

    async def __anext__(self) -> str:
        try:
            return next(self._frames)
        except StopIteration:
            raise StopAsyncIteration from None

    async def send(self, data: str) -> None:
        return None

    async def close(self) -> None:
        return None


def _message(sender: str, body: str, cursor: int) -> str:
    frame = {
        "id": cursor,
        "event": "message",
        "data": {"payload": {"sender": "@switch-agent-1:x", "sender_name": sender, "body": body}},
    }
    return json.dumps(frame)


def test_tap_keeps_a_masked_copy_of_each_message_and_skips_junk() -> None:
    frames = [
        _message("bob-codex", "@bailiff open case x password=hunter2", 1),
        "not json",
        json.dumps({"event": "ping"}),
        _message("alice-claude", "plain reply", 2),
    ]

    async def dial(url: str, headers: dict[str, str]) -> _FakeWs:
        return _FakeWs(frames)

    transcript: list[str] = []

    async def run() -> None:
        # max_reconnects=0: the canned socket drops once, then the tap gives up cleanly
        async with SwitchConnection(
            "http://switch.test", "agent", "key", "cid", ["room"], max_reconnects=0, dial=dial
        ) as conn:
            async for _ in _Tap(conn, transcript).events():
                pass

    with pytest.raises(ReconnectExhausted):
        asyncio.run(run())
    assert transcript[0].startswith("[bob-codex] @bailiff open case x ")
    assert "[redacted" in transcript[0]
    assert "hunter2" not in "\n".join(transcript)
    assert transcript[1] == "[alice-claude] plain reply"


class _Joined:
    """A FakeRoom connection shaped like a live SwitchConnection: run_live waits on `generation`."""

    generation = 1

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    async def __aenter__(self) -> _Joined:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


@pytest.fixture
def live_room(monkeypatch: pytest.MonkeyPatch) -> FakeRoom:
    room = FakeRoom()

    async def register(http: httpx.AsyncClient, name: str) -> tuple[str, str]:
        return name, "key"

    async def create_room(base: str, bailiff: tuple[str, str], names: list[str]) -> str:
        return "room-live"

    def join(base: str, agent_id: str, key: str, cid: str, rooms: list[str]) -> _Joined:
        return _Joined(room.join(agent_id))

    monkeypatch.setattr(live, "_register", register)
    monkeypatch.setattr(live, "_create_room", create_room)
    monkeypatch.setattr(live, "SwitchConnection", join)
    return room


@pytest.mark.asyncio
async def test_a_live_case_writes_the_transcript_and_the_receipt(
    live_room: FakeRoom, tmp_path: Path
) -> None:
    receipt = await asyncio.wait_for(live.run_live("http://switch.test", "tok", tmp_path), 30)
    transcript = (tmp_path / "transcript.txt").read_text(encoding="utf-8").splitlines()
    assert transcript[0].startswith("[pc-live-bob] !open case export-service 500")
    assert receipt["baseline"]["outcome"] == "pass"
    saved = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    assert saved["case_id"] == receipt["case_id"]


@pytest.mark.asyncio
async def test_a_silent_bob_stalls_into_a_named_error_and_every_task_is_done(
    live_room: FakeRoom, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    real_serve_machine = live.serve_machine

    async def silent_bob(
        conn: Any, room_id: str, machine: str, handle: str, run: Any, bailiff: str
    ) -> None:
        if machine == "bob":
            await asyncio.Event().wait()
        await real_serve_machine(conn, room_id, machine, handle, run, bailiff)

    created: list[asyncio.Task[Any]] = []
    real_create_task = asyncio.create_task

    def spy(coro: Any, **kwargs: Any) -> asyncio.Task[Any]:
        task = real_create_task(coro, **kwargs)
        created.append(task)
        return task

    monkeypatch.setattr(live, "serve_machine", silent_bob)
    monkeypatch.setattr(live, "CASE_TIMEOUT_S", 0.1)
    monkeypatch.setattr(live.asyncio, "create_task", spy)
    with pytest.raises(LiveError, match="stalled"):
        await live.run_live("http://switch.test", "tok", tmp_path)
    assert len(created) == 4  # alice, bob, the case, and the case's event pump
    assert all(task.done() for task in created)
    assert not (tmp_path / "receipt.json").exists()


@pytest.mark.asyncio
async def test_an_agent_that_never_connects_is_a_named_error(
    live_room: FakeRoom, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def join(base: str, agent_id: str, key: str, cid: str, rooms: list[str]) -> _Joined:
        conn = _Joined(live_room.join(agent_id))
        if agent_id == "pc-live-bob":
            conn.generation = None  # bob's socket never subscribes
        return conn

    monkeypatch.setattr(live, "SwitchConnection", join)
    monkeypatch.setattr(live, "READY_TIMEOUT_S", 0.1)
    with pytest.raises(LiveError, match=r"did not connect within 0.1 s \(check agent keys"):
        await live.run_live("http://switch.test", "tok", tmp_path)
    assert not (tmp_path / "receipt.json").exists()
