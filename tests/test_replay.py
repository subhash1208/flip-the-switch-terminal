from pathlib import Path
from typing import Any

import pytest

from bailiff.ablation import classify, plan_ablation
from bailiff.fingerprint import diff_fingerprints, parse_fingerprint
from bailiff.models import AblationStep, Runner, StepResult
from bailiff.receipt import build_receipt, save_receipt, step_to_dict
from bailiff.replay import docker_runner, main, replay

ALICE_PROBES = {
    "uname -a": "Linux alice-box 6.8.0 #1 SMP x86_64 GNU/Linux",
    "node -v": "v22.11.0",
    "printenv TZ": "Asia/Kolkata",
    "printenv NODE_OPTIONS": "",
    "stat -f -c %T .": "overlayfs",
    "diskutil info /": "",
    "sha256sum package-lock.json": "aaa111  package-lock.json",
    "env": "PATH=/usr/bin\nAPI_KEY=supersecret\n",
}
BOB_PROBES = {
    "uname -a": "Linux bob-staging 6.8.0 #1 SMP x86_64 GNU/Linux",
    "node -v": "v18.20.4",
    "printenv TZ": "UTC",
    "printenv NODE_OPTIONS": "--openssl-legacy-provider",
    "stat -f -c %T .": "overlayfs",
    "diskutil info /": "",
    "sha256sum package-lock.json": "aaa111  package-lock.json",
    "env": "PATH=/usr/bin\nAPI_KEY=supersecret\n",
}
NODE22 = ["/opt/node22/bin/node", "test.js"]


def node22_passes(runner: Runner) -> tuple[int, str]:
    if runner.cmd == NODE22:
        return 0, ""
    return 1, "TypeError: toSorted is not a function"


def always_zero(runner: Runner) -> tuple[int, str]:
    return 0, ""


def _outcome(exit_code: int) -> str:
    return "pass" if exit_code == 0 else "fail"


def _receipt_file(tmp_path: Path) -> str:
    base = Runner("node:18-bookworm-slim", {}, ["node", "test.js"])
    node = AblationStep(
        "ablation-1", "bob", "node", "v18.20.4", "v22.11.0", Runner(base.image, {}, NODE22)
    )
    tz = AblationStep(
        "ablation-2",
        "bob",
        "tz",
        "UTC",
        "Asia/Kolkata",
        Runner(base.image, {"TZ": "Asia/Kolkata"}, base.cmd),
    )
    case: dict[str, Any] = {
        "case_id": "101",
        "created_at": "2026-11-06T12:00:00+05:30",
        "room_id": "room-101",
        "pinned": {"app_commit": "abc1234", "images": {"alice": "a", "bob": "b"}},
        "baseline": {
            "machine": "alice",
            "cmd": ["node", "test.js"],
            "exit_code": 0,
            "outcome": "pass",
            "stderr_excerpt": "",
        },
        "failure": {
            "machine": "bob",
            "cmd": ["node", "test.js"],
            "exit_code": 1,
            "outcome": "fail",
            "stderr_excerpt": "TypeError",
        },
        "steps": [step_to_dict(node, 0, "pass"), step_to_dict(tz, 1, "fail")],
        "suspects": [],
        "culprit": {"variable": "node", "evidence_step": "ablation-1"},
        "fix": {"branch": "fix/case-101-import", "verified_on": "bob", "outcome": "pass"},
        "attestations": [],
        "redactions": 0,
    }
    path = tmp_path / "receipt.json"
    save_receipt(build_receipt(case), str(path))
    return str(path)


def test_end_to_end_fingerprint_to_matched_replay(tmp_path: Path) -> None:
    suspects = diff_fingerprints(
        parse_fingerprint("alice", ALICE_PROBES), parse_fingerprint("bob", BOB_PROBES)
    )
    steps = plan_ablation(suspects)
    results: list[StepResult] = []
    for step in steps:
        exit_code, _stderr = node22_passes(step.runner)
        results.append(StepResult(step.id, exit_code, _outcome(exit_code), True))
    classified = classify(suspects, results)
    culprit = next(s for s in classified if s.verdict == "culprit")
    evidence = next(
        step for step, result in zip(steps, results, strict=True) if result.outcome == "pass"
    )
    assert culprit.name == "node"
    assert evidence.variable == "node"

    case: dict[str, Any] = {
        "case_id": "101",
        "created_at": "2026-11-06T12:00:00+05:30",
        "room_id": "room-101",
        "pinned": {"app_commit": "abc1234", "images": {"alice": "a", "bob": "b"}},
        "baseline": {
            "machine": "alice",
            "cmd": ["node", "test.js"],
            "exit_code": 0,
            "outcome": "pass",
            "stderr_excerpt": "",
        },
        "failure": {
            "machine": "bob",
            "cmd": ["node", "test.js"],
            "exit_code": 1,
            "outcome": "fail",
            "stderr_excerpt": "TypeError",
        },
        "steps": [
            step_to_dict(step, result.exit_code, result.outcome)
            for step, result in zip(steps, results, strict=True)
        ],
        "suspects": [
            {"name": s.name, "alice": s.alice, "bob": s.bob, "verdict": s.verdict}
            for s in classified
        ],
        "culprit": {"variable": culprit.name, "evidence_step": evidence.id},
        "fix": {"branch": "fix/case-101-import", "verified_on": "bob", "outcome": "pass"},
        "attestations": [],
        "redactions": 1,
    }
    path = tmp_path / "receipt.json"
    save_receipt(build_receipt(case), str(path))

    replayed = replay(str(path), node22_passes)
    assert [r.id for r in replayed] == [s.id for s in steps]
    assert all(r.matched for r in replayed)


def test_cli_exits_zero_when_every_step_matches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main([_receipt_file(tmp_path)], runner_fn=node22_passes)
    out = capsys.readouterr().out
    assert code == 0
    assert "ablation-1: ok" in out
    assert "ablation-2: ok" in out
    assert "2/2 steps matched" in out


def test_mismatch_is_reported_and_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _receipt_file(tmp_path)
    matched = [r.matched for r in replay(path, always_zero)]
    assert matched == [True, False]
    code = main([path], runner_fn=always_zero)
    out = capsys.readouterr().out
    assert code == 1
    assert "ablation-2: MISMATCH" in out
    assert "1/2 steps matched" in out


def test_cli_without_runner_or_docker_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([_receipt_file(tmp_path)]) == 2
    assert "--docker" in capsys.readouterr().err


def test_cli_rejects_an_invalid_receipt(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "receipt.json"
    path.write_text('{"schema_version": 1}', encoding="utf-8")
    assert main([str(path)], runner_fn=node22_passes) == 2
    assert "invalid receipt" in capsys.readouterr().err


def test_docker_runner_refuses_flag_like_image() -> None:
    with pytest.raises(ValueError, match="docker flag"):
        docker_runner(Runner("--privileged", {}, ["node", "test.js"]))


def test_docker_runner_builds_argv_and_maps_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    from bailiff import replay as replay_module

    seen: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(replay_module.subprocess, "run", fake_run)
    runner = Runner("node:22-bookworm-slim", {"TZ": "Asia/Kolkata"}, ["node", "test.js"])
    assert docker_runner(runner) == (0, "")
    assert seen[0][:4] == ["docker", "run", "--rm", "--name"]
    assert seen[0][4].startswith("paritycourt-replay-")
    assert seen[0][5:] == ["-e", "TZ=Asia/Kolkata", "node:22-bookworm-slim", "node", "test.js"]

    def timeout_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(argv, timeout=1)

    monkeypatch.setattr(replay_module.subprocess, "run", timeout_run)
    code, _stderr = docker_runner(runner)
    assert code == 124


def test_docker_runner_refuses_off_list_commands_without_running_docker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from bailiff import replay as replay_module

    def must_not_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"docker ran a refused command: {argv}")

    monkeypatch.setattr(replay_module.subprocess, "run", must_not_run)
    code, stderr = docker_runner(Runner("node:22-bookworm-slim", {}, ["rm", "-rf", "/"]))
    assert code == 126
    assert "allow-list" in stderr
    code, stderr = docker_runner(
        Runner("node:22-bookworm-slim", {"LD_PRELOAD": "x.so"}, ["node", "test.js"])
    )
    assert code == 126
    assert "allow-list" in stderr


def test_a_timed_out_run_removes_its_named_container(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    from bailiff import replay as replay_module

    seen: list[list[str]] = []

    def run_then_time_out(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        if argv[:2] == ["docker", "run"]:
            raise subprocess.TimeoutExpired(argv, timeout=1)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(replay_module.subprocess, "run", run_then_time_out)
    code, _stderr = docker_runner(Runner("node:22-bookworm-slim", {}, ["node", "test.js"]))
    name = seen[0][seen[0].index("--name") + 1]
    assert code == 124
    assert seen[1] == ["docker", "rm", "-f", name]
