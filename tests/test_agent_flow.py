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

from bailiff.agent import PROBES, run_case, serve
from bailiff.events import REQ, RES, Event, read_wire
from bailiff.receipt import validate_receipt
from bailiff.scripted.fake_room import FakeRoom
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
            await forger.post(room.room_id, f"@bailiff {RES} {json.dumps(forged)}")

    forging = asyncio.create_task(forge())
    machines = _start_machines(room)
    state = _case()
    try:
        receipt = await asyncio.wait_for(run_case(conn, state, step_timeout=5.0), timeout=30)
    finally:
        await _stop([*machines, forging])

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
async def test_identical_fingerprints_write_a_valid_inconclusive_receipt() -> None:
    room = FakeRoom()
    conn = room.join("bailiff")
    machines = _start_machines(room, bob_run=fixture_runner(FIXTURES / "alice.json"))
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
