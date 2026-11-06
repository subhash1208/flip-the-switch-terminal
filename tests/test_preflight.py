"""scripts/preflight.py: verdicts and exit codes, with subprocess, PATH and network faked."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import urllib.error
from pathlib import Path
from types import ModuleType

import pytest

PREFLIGHT = Path(__file__).resolve().parent.parent / "scripts" / "preflight.py"
SECRET = "sk-test-SECRET-value-123"
BASE_URL = "http://bailiff.example:8000"


class _FakeResponse:
    status = 200

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


@pytest.fixture
def preflight(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec = importlib.util.spec_from_file_location("preflight", PREFLIGHT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # @dataclass resolves its module through sys.modules while the file executes.
    monkeypatch.setitem(sys.modules, "preflight", module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def healthy(monkeypatch: pytest.MonkeyPatch, preflight: ModuleType) -> None:
    """Every boundary answers success: env set, docker on PATH, subprocesses 0, /health 200."""
    monkeypatch.setenv("BAILIFF_BASE_URL", BASE_URL)
    monkeypatch.setenv("SWITCH_REGISTRATION_TOKEN", SECRET)
    monkeypatch.setattr(preflight.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda argv, **_: subprocess.CompletedProcess(argv, 0, "", ""),
    )
    monkeypatch.setattr(preflight.urllib.request, "urlopen", lambda url, timeout: _FakeResponse())


def run_main(
    preflight: ModuleType, capsys: pytest.CaptureFixture[str], *args: str
) -> tuple[int, str]:
    code = preflight.main(list(args))
    return code, capsys.readouterr().out


def test_secret_value_and_base_url_are_never_printed(
    preflight: ModuleType,
    healthy: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def refuse(url: str, timeout: float) -> None:
        raise urllib.error.URLError(f"connection refused: {url} {SECRET}")

    monkeypatch.setattr(preflight.urllib.request, "urlopen", refuse)
    code, out = run_main(preflight, capsys)
    assert SECRET not in out
    assert "bailiff.example" not in out
    assert "env SWITCH_REGISTRATION_TOKEN: set" in out
    assert "FAIL bailiff reachable: no HTTP response from /health (URLError)" in out
    assert code == 1


def test_missing_docker_is_fail_and_exit_1(
    preflight: ModuleType,
    healthy: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(preflight.shutil, "which", lambda name: None if name == "docker" else "/x")
    code, out = run_main(preflight, capsys)
    assert code == 1
    assert "FAIL docker: docker not on PATH" in out


def test_docker_info_timeout_is_fail_not_traceback(
    preflight: ModuleType,
    healthy: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def slow(argv: list[str], **_: object) -> None:
        raise subprocess.TimeoutExpired(argv, 60)

    monkeypatch.setattr(preflight.subprocess, "run", slow)
    code, out = run_main(preflight, capsys)
    assert code == 1
    assert "FAIL docker: docker info timed out or failed to start" in out


def test_network_timeout_is_fail_not_traceback(
    preflight: ModuleType,
    healthy: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def slow(url: str, timeout: float) -> None:
        raise TimeoutError("timed out")

    monkeypatch.setattr(preflight.urllib.request, "urlopen", slow)
    code, out = run_main(preflight, capsys)
    assert code == 1
    assert "FAIL bailiff reachable: no HTTP response from /health (TimeoutError)" in out


def test_skip_network_warns_without_probing(
    preflight: ModuleType,
    healthy: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def must_not_be_called(url: str, timeout: float) -> None:
        raise AssertionError("--skip-network must not probe")

    monkeypatch.setattr(preflight.urllib.request, "urlopen", must_not_be_called)
    code, out = run_main(preflight, capsys, "--skip-network")
    assert code == 0
    assert "WARN bailiff reachable: skipped by --skip-network" in out


def test_missing_token_is_fail_and_exit_1(
    preflight: ModuleType,
    healthy: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("SWITCH_REGISTRATION_TOKEN")
    code, out = run_main(preflight, capsys, "--skip-network")
    assert code == 1
    assert "FAIL env SWITCH_REGISTRATION_TOKEN: missing" in out


def test_all_pass_exits_0(
    preflight: ModuleType, healthy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = run_main(preflight, capsys)
    assert code == 0
    assert "PREFLIGHT RESULT: PASS (0 FAIL, 0 WARN)" in out
