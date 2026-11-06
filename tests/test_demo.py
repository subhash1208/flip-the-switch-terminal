"""The offline demo: the planted story end to end, and its replay."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bailiff.demo import main


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
    assert f"replay: {count}/{count} steps matched (fixture replay, not Docker)" in out


def test_live_mode_is_a_marked_todo_that_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--live"]) == 2
    assert (
        "live Switch-room mode is the next step (register agents, then run)"
        in capsys.readouterr().out
    )


def test_running_with_no_mode_flag_refuses_and_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "TODO" in capsys.readouterr().out
