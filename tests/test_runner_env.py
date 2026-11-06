from typing import Any

import pytest

from bailiff.scripted import runner


class _Done:
    returncode = 0
    stdout = ""
    stderr = ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        "MY_CREDENTIAL",
        "PRIVATE_KEY",
        "GH_AUTH",
        "DB_PASSWD",
        "SERVICE_TOKEN",
        "API_KEY",
        "CLIENT_SECRET",
    ],
)
async def test_run_local_strips_every_secret_named_variable(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    seen: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> _Done:
        seen.update(kwargs)
        return _Done()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setenv(name, "hunter2")
    monkeypatch.setenv("KEEP_ME_PLAIN", "yes")
    await runner.run_local(["echo"], {})
    assert name not in seen["env"]
    assert seen["env"]["KEEP_ME_PLAIN"] == "yes"
