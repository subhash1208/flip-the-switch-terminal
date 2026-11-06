"""run_local: the child process never inherits secret-looking environment variables."""

from __future__ import annotations

import json
import sys

import pytest

from bailiff.scripted.runner import run_local


@pytest.mark.asyncio
async def test_child_process_does_not_inherit_api_keys_or_other_secret_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALICE_API_KEY", "hunter2")
    monkeypatch.setenv("DEPLOY_TOKEN", "abc123")
    monkeypatch.setenv("DB_PASSWORD", "abc123")
    monkeypatch.setenv("KEEP_ME_VISIBLE", "yes")
    code = "import json, os; print(json.dumps(sorted(os.environ)))"
    result = await run_local([sys.executable, "-c", code], {})
    assert result["exit_code"] == 0
    names = set(json.loads(result["stdout"]))
    assert "KEEP_ME_VISIBLE" in names
    assert not {"ALICE_API_KEY", "DEPLOY_TOKEN", "DB_PASSWORD"} & names
