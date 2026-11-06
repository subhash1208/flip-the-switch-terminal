"""_main_async: BAILIFF_TURN_CAP comes from the environment, and an invalid receipt exits 1.

Switch is the boundary, so the connection and serve are faked. The env contract and exit codes
are real.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bailiff import agent
from bailiff.transport import SwitchRefused


class _FakeConnection:
    async def __aenter__(self) -> _FakeConnection:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


@pytest.fixture
def switch_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("ROOM_ID", "room-1")
    monkeypatch.setenv("BAILIFF_BASE_URL", "http://switch.test")
    monkeypatch.setenv("BAILIFF_AGENT_ID", "agent-1")
    monkeypatch.setenv("BAILIFF_API_KEY", "abc123")
    monkeypatch.setenv("BAILIFF_CONNECTION_ID", "conn-1")
    receipt = tmp_path / "receipt.json"
    monkeypatch.setenv("RECEIPT_PATH", str(receipt))
    monkeypatch.setattr(agent, "SwitchConnection", lambda *args: _FakeConnection())
    return receipt


@pytest.mark.asyncio
async def test_turn_cap_is_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch, switch_env: Path
) -> None:
    monkeypatch.setenv("BAILIFF_TURN_CAP", "3")
    seen: dict[str, Any] = {}

    async def fake_serve(conn: object, room_id: str, **kwargs: Any) -> dict[str, Any]:
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(agent, "serve", fake_serve)
    assert await agent._main_async() == 0
    assert seen["turn_cap"] == 3
    assert switch_env.exists()


@pytest.mark.asyncio
async def test_turn_cap_is_off_when_the_variable_is_unset(
    monkeypatch: pytest.MonkeyPatch, switch_env: Path
) -> None:
    monkeypatch.delenv("BAILIFF_TURN_CAP", raising=False)
    seen: dict[str, Any] = {}

    async def fake_serve(conn: object, room_id: str, **kwargs: Any) -> dict[str, Any]:
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(agent, "serve", fake_serve)
    assert await agent._main_async() == 0
    assert seen["turn_cap"] is None


@pytest.mark.asyncio
async def test_a_non_numeric_turn_cap_exits_2_before_connecting(
    monkeypatch: pytest.MonkeyPatch, switch_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("BAILIFF_TURN_CAP", "three")

    async def must_not_serve(conn: object, room_id: str, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("serve must not run with a bad turn cap")

    monkeypatch.setattr(agent, "serve", must_not_serve)
    assert await agent._main_async() == 2
    assert "BAILIFF_TURN_CAP must be a whole number" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_an_invalid_receipt_exits_1_with_a_clear_error_and_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, switch_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    async def invalid_serve(conn: object, room_id: str, **kwargs: Any) -> dict[str, Any]:
        raise ValueError("invalid receipt: receipt.steps: must contain at least one step")

    monkeypatch.setattr(agent, "serve", invalid_serve)
    assert await agent._main_async() == 1
    assert "error: invalid receipt: receipt.steps" in capsys.readouterr().out
    assert not switch_env.exists()


@pytest.mark.asyncio
async def test_a_closed_connection_exits_1_with_the_reason(
    monkeypatch: pytest.MonkeyPatch, switch_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    async def closed_serve(conn: object, room_id: str, **kwargs: Any) -> dict[str, Any]:
        raise SwitchRefused("Switch closed the connection: agent deleted")

    monkeypatch.setattr(agent, "serve", closed_serve)
    assert await agent._main_async() == 1
    assert "error: Switch closed the connection: agent deleted" in capsys.readouterr().out
