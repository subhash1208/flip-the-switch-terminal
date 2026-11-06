import pytest

from bailiff.agent import MACHINE_PROBES
from bailiff.agent import PROBES as AGENT_PROBES
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
    ["shasum", "-a", "256", "package-lock.json"],
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


def test_every_agent_probe_is_on_the_allow_list() -> None:
    assert all(is_allowed(argv) for argv in AGENT_PROBES.values())
    assert all(is_allowed(argv) for machine in MACHINE_PROBES.values() for argv in machine.values())


@pytest.mark.parametrize(
    "cmd",
    [
        ["sha256sum", "package-lock.json", "--check"],
        ["sha256sum", "package-lock.json;rm"],
        ["stat", "-f", "-c", "%T", "./"],
        ["diskutil", "info", "/", "x"],
        ["shasum", "-a", "256", "package-lock.json", "--check"],
        ["shasum", "-a", "1", "package-lock.json"],
        ["shasum", "package-lock.json"],
        ["shasum", "-a", "256", "package-lock.json;rm"],
        ["shasum", "-a", "256", "../package-lock.json"],
    ],
)
def test_rejects_near_misses_of_the_probes(cmd: list[str]) -> None:
    assert not is_allowed(cmd)
