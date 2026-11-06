"""A masked suspect is never ablated: the placeholder is not a value.

The scenario is the one from the review: alice and bob differ only in the IP inside NODE_OPTIONS.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from bailiff.ablation import NOT_ABLATED_MASKED
from bailiff.agent import serve
from bailiff.receipt import validate_receipt
from bailiff.scripted.fake_room import FakeRoom
from bailiff.scripted.runner import fixture_runner, serve_machine

FIXTURES = Path(__file__).resolve().parents[1] / "bailiff" / "scripted" / "fixtures"
TRIGGER = "!open case export-service 500 on Ubuntu"
ALICE_OPTS = "--max-old-space-size=4096 --inspect=10.99.88.77:9229"
BOB_OPTS = "--max-old-space-size=4096 --inspect=10.11.12.13:9229"
FAILING = {"exit_code": 1, "stdout": "", "stderr": "AssertionError\n"}


def _machine(
    tmp_path: Path,
    name: str,
    base: str,
    node_options: str,
    test: dict[str, Any] | None = None,
) -> Path:
    data = json.loads((FIXTURES / base).read_text(encoding="utf-8"))
    data["commands"]["printenv NODE_OPTIONS"]["stdout"] = f"{node_options}\n"
    if base == "alice.json":  # Bob built from Alice's host: his own probes answer as hers do
        data["commands"]["stat -f -c %T ."] = {"exit_code": 0, "stdout": "msdos\n"}
        shasum = data["commands"]["shasum -a 256 package-lock.json"]
        data["commands"]["sha256sum package-lock.json"] = shasum
    if test is not None:
        data["commands"]["node test.js"] = test
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


async def _run_case(alice: Path, bob: Path) -> tuple[dict[str, Any], FakeRoom]:
    room = FakeRoom()
    bailiff = room.join("bailiff")
    machines = [
        asyncio.create_task(
            serve_machine(
                room.join("alice-claude"),
                room.room_id,
                "alice",
                "alice-claude",
                fixture_runner(alice),
            )
        ),
        asyncio.create_task(
            serve_machine(
                room.join("bob-codex"), room.room_id, "bob", "bob-codex", fixture_runner(bob)
            )
        ),
    ]
    try:
        room.publish("dana", TRIGGER)
        receipt = await asyncio.wait_for(serve(bailiff, room.room_id, step_timeout=5.0), timeout=30)
    finally:
        for task in machines:
            task.cancel()
        await asyncio.gather(*machines, return_exceptions=True)
    return receipt, room


@pytest.mark.asyncio
async def test_ip_only_difference_is_masked_and_gets_no_ablation_step(tmp_path: Path) -> None:
    alice = _machine(tmp_path, "alice.json", "alice.json", ALICE_OPTS)
    bob = _machine(tmp_path, "bob.json", "alice.json", BOB_OPTS, FAILING)
    receipt, room = await _run_case(alice, bob)

    assert validate_receipt(receipt) == []
    assert [s["name"] for s in receipt["suspects"]] == ["node_options"]
    (suspect,) = receipt["suspects"]
    assert suspect["verdict"] == "unknown"
    assert suspect["note"] == NOT_ABLATED_MASKED
    assert suspect["alice"] == "--max-old-space-size=4096 --inspect=[redacted:ip]:9229"
    assert receipt["steps"] == []
    assert receipt["culprit"] is None
    assert receipt["inconclusive"] is True
    assert receipt["inconclusive_reason"] == "not ablated (value masked): node_options"
    assert not any(
        sender == "bailiff" and '"kind": "ablation"' in text for sender, text in room.messages
    )
    raw = json.dumps(receipt)
    assert "10.99.88.77" not in raw
    assert "10.11.12.13" not in raw


@pytest.mark.asyncio
async def test_masked_suspect_is_skipped_while_a_node_major_difference_is_still_the_culprit(
    tmp_path: Path,
) -> None:
    alice = _machine(tmp_path, "alice.json", "alice.json", ALICE_OPTS)
    bob = _machine(tmp_path, "bob.json", "bob.json", BOB_OPTS)
    receipt, _ = await _run_case(alice, bob)

    assert validate_receipt(receipt) == []
    verdicts = {s["name"]: (s["verdict"], s["note"]) for s in receipt["suspects"]}
    assert verdicts["node_options"] == ("unknown", NOT_ABLATED_MASKED)
    assert verdicts["tz"] == ("decoy", "")
    assert verdicts["node"] == ("culprit", "")
    assert receipt["culprit"] == {"variable": "node", "evidence_step": "ablation-2"}
    assert receipt["fix"]["outcome"] == "pass"
    assert "inconclusive" not in receipt
    assert all("[redacted" not in json.dumps(step["runner"]["env"]) for step in receipt["steps"])
    assert "10.99.88.77" not in json.dumps(receipt)
