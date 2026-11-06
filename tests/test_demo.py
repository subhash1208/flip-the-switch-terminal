"""The offline demo: the planted story end to end, and its replay."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from bailiff import demo
from bailiff.ablation import NOT_ABLATED_MASKED
from bailiff.demo import main
from bailiff.scripted.fake_room import FakeRoom


def test_offline_demo_tells_the_story_and_every_receipt_step_replays(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "receipt.json"
    code = main(["--offline", "--receipt", str(path)])
    out = capsys.readouterr().out
    receipt = json.loads(path.read_text(encoding="utf-8"))
    count = len(receipt["steps"])

    assert code == 0
    assert "SIMULATED: in-process fake room, no Switch server" in out
    assert f"replay: {count}/{count} steps matched" in out
    assert {step["variable"]: step["outcome"] for step in receipt["steps"]} == {
        "tz": "fail",
        "node": "pass",
        "node_options": "fail",
        "os (no-op)": "fail",
    }
    assert receipt["culprit"] == {"variable": "node", "evidence_step": "ablation-2"}
    assert receipt["fix"] == {"branch": None, "verified_on": "bob", "outcome": "pass"}
    assert receipt["redactions"] > 0
    assert receipt["simulated"] is True
    assert "inconclusive" not in receipt
    assert {a["machine"] for a in receipt["attestations"]} == {"alice", "bob"}
    assert all("auto-approved" in a["approval"] for a in receipt["attestations"])
    verdicts = {s["name"]: s["verdict"] for s in receipt["suspects"]}
    assert verdicts["os"] == "unknown"
    assert "not ablated (no-op, verdict unknown): os" in out
    privacy = [line for line in out.splitlines() if line.startswith("privacy: ")]
    assert len(privacy) == 1
    assert re.fullmatch(
        r"privacy: masked (\w+=\d+)(, \w+=\d+)* \(placeholders seen in the room transcript\)",
        privacy[0],
    )
    example = [line for line in out.splitlines() if line.startswith("masked example: ")]
    assert len(example) == 1
    assert "[redacted" in example[0]
    assert len(example[0].removeprefix("masked example: ")) <= 100
    written = path.read_text(encoding="utf-8")
    for raw in ("alice@example.com", "/Users/alice", "alice-mac", "10.20.30.40", "hunter2"):
        assert raw not in written
    assert f"replay: {count}/{count} steps matched (fixture replay, not Docker)" in out


def test_offline_receipt_carries_a_privacy_record_that_matches_the_printed_counts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "receipt.json"
    assert main(["--offline", "--receipt", str(path)]) == 0
    out = capsys.readouterr().out
    privacy = json.loads(path.read_text(encoding="utf-8"))["privacy"]

    assert "[redacted:" in privacy["example"]
    assert len(privacy["example"]) <= 100
    (line,) = [text for text in out.splitlines() if text.startswith("privacy: masked ")]
    counts_text = line.removeprefix("privacy: masked ").split(" (")[0]
    printed = {kind: int(n) for kind, n in (part.split("=") for part in counts_text.split(", "))}
    assert printed == privacy["placeholders"]
    raw = json.dumps(privacy)
    for fixture_pii in (
        "alice@example.com",
        "bob@example.org",
        "10.20.30.40",
        "192.168.1.20",
        "hunter2-alice",
        "hunter2-bob",
        "alice-mac.local",
        "bob-staging",
    ):
        assert fixture_pii not in raw
    assert "not ablated (value masked)" not in out


def test_a_value_masked_suspect_is_named_on_its_own_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def masked_run(*_: object) -> tuple[dict[str, Any], FakeRoom]:
        suspect = {
            "name": "node_options",
            "alice": "[redacted]",
            "bob": "[redacted]",
            "verdict": "unknown",
            "note": NOT_ABLATED_MASKED,
        }
        receipt = {
            "case_id": "case-masked",
            "suspects": [suspect],
            "steps": [],
            "culprit": None,
            "fix": None,
            "redactions": 2,
        }
        return receipt, FakeRoom()

    def no_steps(path: str, runner_fn: object) -> list[object]:
        return []

    monkeypatch.setattr(demo, "run_offline", masked_run)
    monkeypatch.setattr(demo, "replay", no_steps)
    assert main(["--offline", "--receipt", str(tmp_path / "r.json")]) == 0
    out = capsys.readouterr().out
    assert "not ablated (value masked): node_options" in out
    assert "not ablated (no-op, verdict unknown): none" in out


def test_live_mode_is_a_marked_todo_that_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--live"]) == 2
    assert (
        "live Switch-room mode is the next step (register agents, then run)"
        in capsys.readouterr().out
    )


def test_running_with_no_mode_flag_refuses_and_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "TODO" in capsys.readouterr().out
