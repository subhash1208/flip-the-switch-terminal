import pytest

from bailiff.allowlist import ENV_OVERLAY_KEYS, is_allowed, is_allowed_overlay

PROBES = [
    ["uname", "-a"],
    ["node", "-v"],
    ["git", "config", "core.ignorecase"],
    ["printenv", "TZ"],
    ["printenv", "NODE_OPTIONS"],
    ["stat", "-f", "-c", "%T", "."],
    ["diskutil", "info", "/"],
    ["sha256sum", "package-lock.json"],
    ["env"],
    ["node", "test.js"],
    ["/opt/node22/bin/node", "test.js"],
]


@pytest.mark.parametrize("cmd", PROBES)
def test_accepts_each_allow_listed_command(cmd: list[str]) -> None:
    assert is_allowed(cmd)


@pytest.mark.parametrize(
    "cmd",
    [
        ["cat", ".env"],
        ["env", ";", "rm", "-rf", "/"],
        ["uname", "-a", "-s"],
        ["printenv", "PATH"],
        ["node", "-e", "process.exit(0)"],
        ["uname -a"],
        [],
        "uname -a",
        ("uname", "-a"),
        ["uname", ["-a"]],
    ],
)
def test_rejects_anything_off_the_list(cmd: object) -> None:
    assert not is_allowed(cmd)


def test_overlay_allows_only_tz_and_node_options() -> None:
    assert {"TZ", "NODE_OPTIONS"} == ENV_OVERLAY_KEYS
    assert is_allowed_overlay({})
    assert is_allowed_overlay({"TZ": "UTC", "NODE_OPTIONS": "--openssl-legacy-provider"})
    assert not is_allowed_overlay({"TZ": "UTC", "PATH": "/tmp"})
    assert not is_allowed_overlay({"LD_PRELOAD": "/tmp/evil.so"})
