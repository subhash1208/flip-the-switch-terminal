"""The Bailiff flow end to end against the in-memory room and the scripted machines.

No Switch and no LLM. The command runner is the boundary: Alice and Bob answer from fixture files.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

from bailiff.agent import PROBES, _doc_id, _participant_ids, run_case, serve
from bailiff.events import REQ, RES, Event, read_wire
from bailiff.receipt import validate_receipt
from bailiff.scripted.fake_room import FakeConnection, FakeRoom
from bailiff.scripted.runner import Runner, fixture_runner, serve_machine
from bailiff.state import CaseState
from bailiff.transport import TakenOver

FIXTURES = Path(__file__).resolve().parents[1] / "bailiff" / "scripted" / "fixtures"
APPROVAL = "APPROVAL: auto-approved (scripted agent, no human)"


def _start_machines(room: FakeRoom, bob_run: Runner | None = None) -> list[asyncio.Task[None]]:
    bob = bob_run or fixture_runner(FIXTURES / "bob.json")
    return [
        asyncio.create_task(
            serve_machine(
                room.join("alice-claude"),
                room.room_id,
                "alice",
                "alice-claude",
                fixture_runner(FIXTURES / "alice.json"),
            )
        ),
        asyncio.create_task(
            serve_machine(room.join("bob-codex"), room.room_id, "bob", "bob-codex", bob)
        ),
    ]


def _alice_twin(tmp_path: Path) -> Path:
    """Alice's fixture with Bob's own probes answered as Alice's are: two identical hosts."""
    data = json.loads((FIXTURES / "alice.json").read_text(encoding="utf-8"))
    data["commands"]["stat -f -c %T ."] = {"exit_code": 0, "stdout": "msdos\n"}
    shasum = data["commands"]["shasum -a 256 package-lock.json"]
    data["commands"]["sha256sum package-lock.json"] = shasum
    path = tmp_path / "twin.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


async def _stop(tasks: list[asyncio.Task[None]]) -> None:
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def _case() -> CaseState:
    return CaseState(
        case_id="case-t1", room_id="room-offline", title="export-service 500", opened_by="dana"
    )


def _slow_node(inner: Runner, seconds: float) -> Runner:
    async def run(argv: list[str], overlay: dict[str, str]) -> dict[str, Any]:
        if any("/opt/node22" in part for part in argv):
            await asyncio.sleep(seconds)
        return await inner(argv, overlay)

    return run


@pytest.mark.asyncio
async def test_full_case_runs_end_to_end_from_a_trigger_and_yields_a_valid_receipt() -> None:
    room = FakeRoom()
    bailiff = room.join("bailiff")
    machines = _start_machines(room)
    try:
        room.publish("dana", "chatter before the trigger")
        room.publish("dana", "!open case export-service 500 on Ubuntu")
        receipt = await asyncio.wait_for(serve(bailiff, room.room_id, step_timeout=5.0), timeout=30)
    finally:
        await _stop(machines)

    assert receipt["baseline"]["outcome"] == "pass"
    assert receipt["failure"]["outcome"] == "fail"
    passing = [s for s in receipt["steps"] if s["outcome"] == "pass"]
    assert receipt["culprit"]["evidence_step"] == passing[0]["id"]
    assert {a["machine"] for a in receipt["attestations"]} == {"alice", "bob"}
    assert receipt["redactions"] >= 1
    assert any(APPROVAL in text for _, text in room.messages)
    assert not any("hunter2" in text for _, text in room.messages)
    (doc,) = room.documents.values()
    assert "hunter2" not in doc
    assert doc.count("```") == 2
    assert '"state": "closed"' in doc


@pytest.mark.asyncio
async def test_malformed_frames_are_skipped_and_counted_while_the_case_runs() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    machines = _start_machines(room)
    state = _case()
    try:
        room.push_raw("bailiff", '{"event": "message", "data": {"payload": "bad"}')
        room.push_raw("bailiff", "not json at all")
        receipt = await asyncio.wait_for(run_case(conn, state, step_timeout=5.0), timeout=30)
    finally:
        await _stop(machines)

    assert state.malformed == 2
    assert state.state == "closed"
    assert receipt["baseline"]["outcome"] == "pass"


@pytest.mark.asyncio
async def test_a_silent_machine_marks_the_step_fail_and_the_case_still_closes() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    slow_bob = _slow_node(fixture_runner(FIXTURES / "bob.json"), seconds=1.0)
    machines = _start_machines(room, bob_run=slow_bob)
    state = _case()
    try:
        receipt = await asyncio.wait_for(run_case(conn, state, step_timeout=0.3), timeout=30)
    finally:
        await _stop(machines)

    timed_out = [s for s in receipt["steps"] if s["exit_code"] is None]
    assert timed_out, "the slowed Node step should have timed out"
    assert all(s["outcome"] == "fail" for s in timed_out)
    assert state.state == "closed"
    assert state.verdict == "no single culprit isolated"


@pytest.mark.asyncio
async def test_probe_outside_the_allow_list_is_refused_and_never_sent_to_a_machine() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    machines = _start_machines(room)
    state = _case()
    probes = {"uname": PROBES["uname"], "evil": ["rm", "-rf", "/"]}
    try:
        await asyncio.wait_for(run_case(conn, state, probes=probes, step_timeout=5.0), timeout=30)
    finally:
        await _stop(machines)

    assert any(p["probe"] == "evil" and p["outcome"] == "refused" for p in state.probes)
    assert any(text.startswith("REFUSED for alice") for _, text in room.messages)
    assert not any('"rm"' in text for _, text in room.messages)


@pytest.mark.asyncio
async def test_each_machine_runs_only_its_own_os_probes_and_the_case_file_is_updated_by_id() -> (
    None
):
    room = FakeRoom()
    conn = room.join("bailiff")
    machines = _start_machines(room)
    state = _case()
    try:
        await asyncio.wait_for(run_case(conn, state, step_timeout=5.0), timeout=30)
    finally:
        await _stop(machines)

    ran = {(p["machine"], p["probe"]) for p in state.probes}
    assert {
        ("alice", "diskutil"),
        ("alice", "shasum"),
        ("bob", "stat"),
        ("bob", "sha256sum"),
    } <= ran
    assert not {probe for m, probe in ran if m == "alice"} & {"stat", "sha256sum"}
    assert not {probe for m, probe in ran if m == "bob"} & {"diskutil", "shasum"}
    alice = state.machines["alice"]["fingerprint"]
    bob = state.machines["bob"]["fingerprint"]
    assert (alice["fs_case"], bob["fs_case"]) == ("case-insensitive", "case-sensitive")
    assert alice["lock_sha"] == bob["lock_sha"] != ""
    assert state.doc_id in room.documents
    assert state.state == "closed"


class _History:
    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._events = events

    async def op(self, operation: str, /, **args: Any) -> dict[str, Any]:
        return {"result": {"threads": [{"root": ev, "replies": []} for ev in self._events]}}


JOIN_BOB = {"kind": "room_join", "sender": "@switch-agent-b:fake", "sender_name": "bob-codex"}


def test_a_handle_resolves_to_the_id_switch_wrote_at_join_not_to_a_message_claiming_the_name() -> (
    None
):
    claim = {"kind": "message", "sender": "@switch-agent-m:fake", "sender_name": "bob-codex"}
    history = _History([JOIN_BOB, claim, JOIN_BOB])
    ids = asyncio.run(_participant_ids(history, "room-1", {"bob": "bob-codex"}))
    assert ids == {"bob": "@switch-agent-b:fake"}


@pytest.mark.parametrize(
    "events, found",
    [([], 0), ([JOIN_BOB, {**JOIN_BOB, "sender": "@switch-agent-x:fake"}], 2)],
)
def test_a_handle_without_exactly_one_join_id_is_a_named_error(
    events: list[dict[str, Any]], found: int
) -> None:
    with pytest.raises(ValueError, match=rf"room_join for bob-codex in the room, found {found}"):
        asyncio.run(_participant_ids(_History(events), "room-1", {"bob": "bob-codex"}))


def test_two_machines_resolving_to_one_participant_id_is_a_named_error() -> None:
    history = _History([JOIN_BOB])
    with pytest.raises(ValueError, match="two machines resolved to the same participant id"):
        asyncio.run(_participant_ids(history, "room-1", {"alice": "bob-codex", "bob": "bob-codex"}))


@pytest.mark.parametrize(
    "reply",
    [
        {"document_id": "d-1"},
        {"id": "d-1"},
        {"result": {"document_id": "d-1"}},
        {"result": {"id": "d-1"}},
    ],
)
def test_create_reply_document_id_is_found_in_each_likely_place(reply: dict[str, Any]) -> None:
    assert _doc_id(reply) == "d-1"


def test_create_reply_without_a_document_id_is_a_named_error() -> None:
    with pytest.raises(ValueError, match=r"reply keys: \['accepted'\]"):
        _doc_id({"accepted": True})


async def _evicted_events() -> AsyncIterator[Event]:
    raise TakenOver("taken over by another connection; not reconnecting")
    yield  # unreachable: makes this an async generator


class _EvictedConnection:
    malformed = 0

    def events(self) -> AsyncIterator[Event]:
        return _evicted_events()


@pytest.mark.asyncio
async def test_taken_over_while_waiting_for_a_trigger_stops_the_flow_and_writes_nothing() -> None:
    with pytest.raises(TakenOver):
        await asyncio.wait_for(
            serve(_EvictedConnection(), "room-offline", step_timeout=5.0), timeout=30
        )  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_a_reply_from_a_third_sender_is_ignored_and_counted() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    forger = room.join("mallory")  # joined first, so its forged reply is queued ahead of Bob's

    async def forge() -> None:
        async for ev in forger.events():
            req = read_wire(ev.text, REQ)
            if req is None or req.get("machine") != "bob":
                continue
            forged = {
                "request_id": req["request_id"],
                "machine": "bob",
                "kind": req["kind"],
                "exit_code": 0,
                "stderr": "forged",
            }
            # Mallory's own id, but the display name Bob uses: a name is not an identity.
            room.publish("mallory", f"@bailiff {RES} {json.dumps(forged)}", display="bob-codex")

    forging = asyncio.create_task(forge())
    machines = _start_machines(room)
    state = _case()
    try:
        receipt = await asyncio.wait_for(run_case(conn, state, step_timeout=5.0), timeout=30)
    finally:
        await _stop([*machines, forging])

    assert receipt["failure"]["outcome"] == "fail"
    assert state.malformed >= 1


class _ForgingAlice:
    """Alice's real connection: it forges Bob's reply, once for each request Bob is sent."""

    def __init__(self, room: FakeRoom, conn: FakeConnection) -> None:
        self._room = room
        self._conn = conn

    async def events(self) -> AsyncIterator[Event]:
        async for ev in self._conn.events():
            req = read_wire(ev.text, REQ)
            if req is not None and req.get("machine") == "bob":
                forged = {
                    "request_id": req["request_id"],
                    "machine": "bob",
                    "kind": req["kind"],
                    "exit_code": 0,
                    "stderr": "forged",
                }
                self._room.publish(
                    "alice-claude", f"@bailiff {RES} {json.dumps(forged)}", display="bob-codex"
                )
            yield ev

    async def post(self, room_id: str, text: str) -> int:
        return await self._conn.post(room_id, text)


@pytest.mark.asyncio
async def test_a_real_machine_forging_the_other_machines_reply_is_refused() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    alice = _ForgingAlice(room, room.join("alice-claude"))
    machines = [
        asyncio.create_task(
            serve_machine(
                alice,
                room.room_id,
                "alice",
                "alice-claude",
                fixture_runner(FIXTURES / "alice.json"),
            )
        ),
        asyncio.create_task(
            serve_machine(
                room.join("bob-codex"),
                room.room_id,
                "bob",
                "bob-codex",
                fixture_runner(FIXTURES / "bob.json"),
            )
        ),
    ]
    state = _case()
    try:
        receipt = await asyncio.wait_for(run_case(conn, state, step_timeout=5.0), timeout=30)
    finally:
        await _stop(machines)

    assert receipt["failure"]["outcome"] == "fail"
    assert state.malformed >= 1


@pytest.mark.asyncio
async def test_a_turn_cap_stops_the_case_and_writes_a_valid_inconclusive_receipt() -> None:
    room = FakeRoom()
    bailiff = room.join("bailiff")
    machines = _start_machines(room)
    try:
        room.publish("dana", "!open case export-service 500")
        receipt = await asyncio.wait_for(
            serve(bailiff, room.room_id, step_timeout=5.0, turn_cap=3), timeout=30
        )
    finally:
        await _stop(machines)

    assert validate_receipt(receipt) == []
    assert receipt["inconclusive"] is True
    assert "turn cap" in receipt["inconclusive_reason"]
    assert receipt["baseline"]["exit_code"] is None
    assert receipt["baseline"]["outcome"] == "fail"
    assert receipt["steps"] == []
    assert receipt["culprit"] is None


@pytest.mark.asyncio
async def test_identical_fingerprints_write_a_valid_inconclusive_receipt(tmp_path: Path) -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    machines = _start_machines(room, bob_run=fixture_runner(_alice_twin(tmp_path)))
    state = _case()
    try:
        receipt = await asyncio.wait_for(run_case(conn, state, step_timeout=5.0), timeout=30)
    finally:
        await _stop(machines)

    assert validate_receipt(receipt) == []
    assert receipt["inconclusive"] is True
    assert receipt["inconclusive_reason"].startswith("no suspects")
    assert receipt["steps"] == []
    assert receipt["baseline"]["outcome"] == "pass"
