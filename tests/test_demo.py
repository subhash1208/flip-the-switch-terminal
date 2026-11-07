"""The offline demo: the planted story end to end, and its replay."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import pytest

from bailiff import demo
from bailiff.ablation import NOT_ABLATED_MASKED
from bailiff.demo import main
from bailiff.live import LiveError
from bailiff.models import StepResult
from bailiff.receipt import save_receipt
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
        "fs_case (no-op)": "fail",
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
    assert "not ablated (no-op, verdict unknown): fs_case, os" in out
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


def test_live_mode_without_config_names_what_is_missing_and_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("BAILIFF_BASE_URL", raising=False)
    monkeypatch.delenv("SWITCH_REGISTRATION_TOKEN", raising=False)
    assert main(["--live"]) == 2
    out = capsys.readouterr().out
    assert "BAILIFF_BASE_URL and SWITCH_REGISTRATION_TOKEN" in out
    assert "SIMULATED" not in out


def test_running_with_no_mode_flag_refuses_and_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "choose a mode: --offline or --live" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("argv", "alice"),
    [(["--live"], None), (["--live", "--alice-agent", "alice-claude"], "alice-claude")],
)
def test_alice_agent_reaches_the_live_run_only_when_given(
    argv: list[str], alice: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str | None] = []

    def live_demo(
        evidence: Path = demo.EVIDENCE, alice_agent: str | None = None, chat_user: str | None = None
    ) -> int:
        seen.append(alice_agent)
        return 0

    monkeypatch.setattr(demo, "run_live_demo", live_demo)
    assert main(argv) == 0
    assert seen == [alice]


@pytest.mark.parametrize("name", ["pc-live-alice", "pc-live-bob", "pc-live-bailiff"])
def test_alice_agent_cannot_reuse_a_scripted_live_name(
    name: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seen: list[str | None] = []

    def live_demo(
        evidence: Path = demo.EVIDENCE, alice_agent: str | None = None, chat_user: str | None = None
    ) -> int:
        seen.append(alice_agent)
        return 0

    monkeypatch.setattr(demo, "run_live_demo", live_demo)
    assert main(["--live", "--alice-agent", name]) == 2
    assert f"error: --alice-agent {name} is a scripted pc-live name" in capsys.readouterr().out
    assert seen == []


def test_alice_agent_without_live_is_refused_and_exits_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--offline", "--alice-agent", "alice-claude"]) == 2
    assert "--alice-agent needs --live" in capsys.readouterr().out


@pytest.fixture
def live_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BAILIFF_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("SWITCH_REGISTRATION_TOKEN", "token-for-test")


def _live_returning(receipt: dict[str, Any]) -> Any:
    """A stand-in for run_live: writes the receipt where the real run would, then returns it."""

    async def live_run(
        base: str,
        token: str,
        evidence: Path,
        alice_agent: str | None = None,
        chat_user: str | None = None,
    ) -> dict[str, Any]:
        save_receipt(receipt, str(evidence / "receipt.json"))
        return receipt

    return live_run


@pytest.mark.parametrize(
    "failure",
    [
        LiveError("server said no"),
        ValueError("expected one room_join for pc-live-bob in the room, found 0"),
    ],
)
def test_a_live_failure_prints_the_reason_and_exits_1(
    failure: Exception,
    live_config: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def refused(
        base: str,
        token: str,
        evidence: Path,
        alice_agent: str | None = None,
        chat_user: str | None = None,
    ) -> dict[str, Any]:
        raise failure

    monkeypatch.setattr(demo, "run_live", refused)
    assert demo.run_live_demo(tmp_path) == 1
    assert f"error: {failure}" in capsys.readouterr().out


def test_a_live_run_that_replays_in_full_exits_0(
    live_config: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    receipt, _ = asyncio.run(demo.run_offline())
    monkeypatch.setattr(demo, "run_live", _live_returning(receipt))
    assert demo.run_live_demo(tmp_path) == 0
    out = capsys.readouterr().out
    assert "LIVE: running against a real Switch server" in out
    assert "replay: 5/5 steps matched (fixture replay, not Docker)" in out


def test_a_live_replay_mismatch_exits_1(
    live_config: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    receipt, _ = asyncio.run(demo.run_offline())
    monkeypatch.setattr(demo, "run_live", _live_returning(receipt))
    missed = StepResult(id="ablation-1", exit_code=1, outcome="fail", matched=False)
    monkeypatch.setattr(demo, "replay", lambda path, runner_fn: [missed])
    assert demo.run_live_demo(tmp_path) == 1
    assert "replay: 0/1 steps matched" in capsys.readouterr().out


def test_a_live_receipt_that_fails_validation_is_a_named_error(
    live_config: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    receipt, _ = asyncio.run(demo.run_offline())
    monkeypatch.setattr(demo, "run_live", _live_returning(receipt))

    def invalid(path: str, runner_fn: object) -> list[StepResult]:
        raise ValueError("invalid receipt: receipt.steps: must contain at least one step")

    monkeypatch.setattr(demo, "replay", invalid)
    assert demo.run_live_demo(tmp_path) == 1
    assert "error: invalid receipt: receipt.steps" in capsys.readouterr().out


def test_chat_user_reaches_the_live_run_only_when_given(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str | None] = []

    def live_demo(
        evidence: Path = demo.EVIDENCE, alice_agent: str | None = None, chat_user: str | None = None
    ) -> int:
        seen.append(chat_user)
        return 0

    monkeypatch.setattr(demo, "run_live_demo", live_demo)
    assert main(["--live", "--chat-user", "user"]) == 0
    assert main(["--live"]) == 0
    assert seen == ["user", None]


def test_chat_user_without_live_is_refused_and_exits_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--offline", "--chat-user", "user"]) == 2
    assert "error: --chat-user needs --live" in capsys.readouterr().out


def test_chat_user_names_the_mattermost_channel_before_the_run(
    live_config: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen: list[str | None] = []

    async def refused(
        base: str,
        token: str,
        evidence: Path,
        alice_agent: str | None = None,
        chat_user: str | None = None,
    ) -> dict[str, Any]:
        seen.append(chat_user)
        raise LiveError("stop before the case")

    monkeypatch.setattr(demo, "run_live", refused)
    assert demo.run_live_demo(tmp_path, chat_user="user") == 1
    assert seen == ["user"]
    assert "LIVE: asking Switch for a Mattermost channel for @user" in capsys.readouterr().out
