"""Live mode: one ParityCourt case run on a real Switch server.

    BAILIFF_BASE_URL=http://127.0.0.1:8000 SWITCH_REGISTRATION_TOKEN=... \
        python -m bailiff.demo --live

Registers the Bailiff and both machine agents under pc-live-* names (a re-run rotates only those
keys), opens a room with the Bailiff's key, and runs the case over real WebSockets. Alice and Bob
are scripted: they answer from the canned fixtures, so the receipt can be replayed against Bob's
fixture. With `alice_agent` (--alice-agent NAME) a Console-registered agent plays Alice instead,
named when the room is created. Agent keys stay in memory; never printed or saved.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

import httpx
import websockets

from bailiff.agent import STEP_TIMEOUT, _participant_ids, serve
from bailiff.events import Event
from bailiff.receipt import save_receipt
from bailiff.redact import mask_bounded
from bailiff.scripted.runner import fixture_runner, serve_machine
from bailiff.transport import SwitchConnection

FIXTURES = Path(__file__).parent / "scripted" / "fixtures"
BAILIFF = "pc-live-bailiff"
LIVE = {"alice": "pc-live-alice", "bob": "pc-live-bob"}
# The trigger is matched by phrase (agent.TRIGGERS), so the opener does not name the Bailiff.
OPENING = "!open case export-service 500 AuthVerifierError on Ubuntu, passes on the Mac"
CASE_TIMEOUT_S = 180.0
READY_TIMEOUT_S = 10.0
# A human approves each probe in Console when a real Alice runs, so the waits grow.
REAL_STEP_TIMEOUT_S = 300.0
REAL_CASE_TIMEOUT_S = 3600.0
JOIN_TIMEOUT_S = 600.0


class LiveError(Exception):
    """The live server refused a call or returned an unusable reply."""


def _register_body(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": "ParityCourt live demo",
        "connector_type": "custom",
        "integration_profile": {
            "connection_model": "always_on",
            "message_exchange": True,
            "pre_invocation_mediation": [],
            "post_invocation_mediation": [],
            "event_reporting": [],
        },
    }


async def _register(http: httpx.AsyncClient, name: str) -> tuple[str, str]:
    body = _register_body(name)
    resp = await http.post("/agents", json=body)
    if resp.status_code == 409:  # already registered: rotate the key
        resp = await http.post("/agents", json={**body, "overwrite": True})
    if not resp.is_success:
        raise LiveError(f"register {name} failed with HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if not isinstance(data, dict) or not {"id", "api_key"} <= data.keys():
        raise LiveError(f"register {name} reply had no id or api_key")
    return str(data["id"]), str(data["api_key"])


def room_id_from(reply: dict[str, Any]) -> str:
    result = reply.get("result")
    room_id = result.get("id") if isinstance(result, dict) else None
    if not isinstance(room_id, str):
        raise LiveError(f"create_room reply has no room id: {str(reply)[:200]}")
    return room_id


async def _create_room(
    base: str, bailiff: tuple[str, str], names: list[str], chat_user: str | None = None
) -> str:
    """create_room needs an open connection, so the Bailiff opens one with no room claimed yet.

    With `chat_user` the room is bridged to the default bridge (Mattermost) and that user is added.
    """
    agent_id, key = bailiff
    cid = str(uuid.uuid4())
    auth = {"Authorization": f"Bearer {key}"}
    scheme_base = base.replace("http", "ws", 1)  # http->ws, https->wss
    url = f"{scheme_base}/agents/{agent_id}/connection/ws?connection_id={cid}&filter=all&rooms="
    body: dict[str, Any] = {
        "name": f"paritycourt-live-{uuid.uuid4().hex[:8]}",
        "description": "ParityCourt live case",
        "agent_names": names,
    }
    if chat_user:
        body["user_names"] = [chat_user]
    else:
        body["internal_only"] = True
    async with websockets.connect(url, additional_headers=auth) as ws:
        try:
            async with asyncio.timeout(READY_TIMEOUT_S):
                await ws.recv()  # connection_state: ops are refused until the socket is open
        except TimeoutError:
            raise LiveError(
                f"no connection_state from Switch within {READY_TIMEOUT_S:g} s"
                " (check agent keys / server)"
            ) from None
        async with httpx.AsyncClient(base_url=base, timeout=10) as http:
            resp = await http.post(
                f"/agents/{agent_id}/ops/create_room",
                headers={**auth, "X-Switch-Connection-Id": cid},
                json=body,
            )
    if not resp.is_success:
        raise LiveError(f"create_room failed with HTTP {resp.status_code}: {resp.text[:200]}")
    return room_id_from(resp.json())


class _Tap:
    """The Bailiff's connection, with a masked copy of each room message kept for the transcript."""

    def __init__(self, conn: SwitchConnection, transcript: list[str]) -> None:
        self._conn = conn
        self._transcript = transcript

    @property
    def malformed(self) -> int:
        return self._conn.malformed

    @malformed.setter
    def malformed(self, value: int) -> None:
        self._conn.malformed = value

    async def events(self) -> AsyncIterator[Event]:
        async for ev in self._conn.events():
            if ev.text is not None:
                name = ev.sender_name or "unknown"
                self._transcript.append(f"[{name}] {mask_bounded(ev.text)[0]}")
            yield ev

    async def op(self, operation: str, /, **args: Any) -> dict[str, Any]:
        return await self._conn.op(operation, **args)

    async def post(self, room_id: str, text: str) -> int:
        return await self._conn.post(room_id, text)


async def _await_join(bailiff: SwitchConnection, room: str, handle: str) -> None:
    """Wait until Switch writes the room_join for the agent named when the room was created."""
    last = "no read_context reply"
    try:
        async with asyncio.timeout(JOIN_TIMEOUT_S):
            while True:
                try:
                    await _participant_ids(bailiff, room, {"alice": handle})
                    return
                except ValueError as exc:  # no join yet, or a duplicate join: keep the cause
                    last = str(exc)
                    await asyncio.sleep(2.0)
    except TimeoutError:
        raise LiveError(
            f"@{handle} did not join the room within {JOIN_TIMEOUT_S:g} s (last: {last})"
        ) from None


async def run_live(
    base: str,
    token: str,
    evidence: Path,
    alice_agent: str | None = None,
    chat_user: str | None = None,
) -> dict[str, Any]:
    """Run one case on `base`; writes transcript.txt and receipt.json to `evidence`.

    `alice_agent` is a Console-registered agent that plays Alice in place of the scripted one.
    Nothing registers or connects it: it is named in create_room, and Switch must accept that.
    `chat_user` makes the room a Mattermost channel with that user in it, visible in Console.
    """
    scripted = not alice_agent
    alice = alice_agent or LIVE["alice"]
    registered = (BAILIFF, *LIVE.values()) if scripted else (BAILIFF, LIVE["bob"])
    names = list(registered) if scripted else [*registered, alice]
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(base_url=base, timeout=10, headers=headers) as http:
        keys = {name: await _register(http, name) for name in registered}
    try:
        room = await _create_room(base, keys[BAILIFF], names, chat_user)
    except LiveError as exc:
        if chat_user:
            text = str(exc).lower()
            hint = ""
            if "turned off" in text or "channel creation" in text:
                hint = " (allow channel creation for this connection in Console)"
            elif "bridge" in text:
                hint = " (is the default Mattermost bridge running?)"
            who = f" with @{alice_agent}" if alice_agent else ""
            raise LiveError(
                f"could not create a Mattermost room for {chat_user}{who}: {exc}{hint}"
            ) from exc
        if scripted:
            raise
        raise LiveError(f"could not create the room with @{alice}: {exc}") from exc
    print(f"room: {room}")

    def connect(agent: str) -> SwitchConnection:
        agent_id, key = keys[agent]
        return SwitchConnection(base, agent_id, key, str(uuid.uuid4()), [room])

    transcript: list[str] = []
    handles = {"alice": alice, "bob": LIVE["bob"]}
    step_timeout = STEP_TIMEOUT if scripted else REAL_STEP_TIMEOUT_S
    case_timeout = CASE_TIMEOUT_S if scripted else REAL_CASE_TIMEOUT_S
    async with AsyncExitStack() as stack:
        conns = {name: await stack.enter_async_context(connect(name)) for name in registered}
        bailiff, bob = conns[BAILIFF], conns[LIVE["bob"]]
        machines: list[asyncio.Task[None]] = []
        if scripted:
            machines.append(
                asyncio.create_task(
                    serve_machine(
                        conns[alice],
                        room,
                        "alice",
                        alice,
                        fixture_runner(FIXTURES / "alice.json"),
                        BAILIFF,
                    )
                )
            )
        machines.append(
            asyncio.create_task(
                serve_machine(
                    bob, room, "bob", LIVE["bob"], fixture_runner(FIXTURES / "bob.json"), BAILIFF
                )
            )
        )
        case = asyncio.create_task(
            serve(_Tap(bailiff, transcript), room, machines=handles, step_timeout=step_timeout)
        )
        try:
            # The opening must not go out before every socket is subscribed (start_from=head).
            try:
                async with asyncio.timeout(READY_TIMEOUT_S):
                    while any(c.generation is None for c in conns.values()):
                        await asyncio.sleep(0.05)
            except TimeoutError:
                raise LiveError(
                    f"agents did not connect within {READY_TIMEOUT_S:g} s"
                    " (check agent keys / server)"
                ) from None
            if not scripted:
                print(
                    f"waiting for @{alice} to join {room} (it was named when the room was created);"
                    f' if it does not answer, check Console\'s "Who can talk to your agent"'
                    f" for {alice}"
                )
                await _await_join(bailiff, room, alice)
            await bob.post(room, OPENING)
            try:
                receipt = await asyncio.wait_for(case, case_timeout)
            except TimeoutError:
                raise LiveError(
                    f"no receipt within {case_timeout:.0f} s: the case stalled"
                ) from None
        finally:
            for task in (*machines, case):
                task.cancel()
            await asyncio.gather(*machines, case, return_exceptions=True)
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "transcript.txt").write_text("\n".join(transcript) + "\n", encoding="utf-8")
    save_receipt(receipt, str(evidence / "receipt.json"))
    return receipt
