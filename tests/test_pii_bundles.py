"""Realistic machine bundles, masked end to end: parse, room document, receipt."""

from __future__ import annotations

import json
from pathlib import Path

from bailiff.demo import FIXTURES, run_offline
from bailiff.fingerprint import diff_fingerprints, parse_fingerprint

MAC_UNAME = "Darwin alices-mac.local 24.5.0 Darwin Kernel Version 24.5.0 arm64"
LINUX_UNAME = "Linux bob-staging 6.8.0-45-generic #45-Ubuntu SMP x86_64 GNU/Linux"
MAC_ENV = (
    "HOME=/Users/alice\n"
    "USER=alice\n"
    "HOSTNAME=alices-mac.local\n"
    "EMAIL=alice@example.com\n"
    "SSH_CLIENT=10.20.30.40 52211 22\n"
    "IFACE_MAC=00:1b:44:11:3a:b7\n"
    "IPV6_ADDR=2001:db8::5\n"
    "DB_PASSWORD=correct horse battery\n"
    "DATABASE_PASSWORD=hunter2-alice\n"
    "TZ=Europe/London\n"
)
LINUX_ENV = (
    "HOME=/home/bob\n"
    "USER=bob\n"
    "HOSTNAME=bob-staging\n"
    "EMAIL=bob@example.org\n"
    "SSH_CLIENT=192.168.1.20 40022 22\n"
    "IFACE_MAC=00-1B-44-11-3A-B8\n"
    "DB_PASSWORD=correct horse battery\n"
    "DATABASE_PASSWORD=hunter2-bob\n"
    "TZ=UTC\n"
)
MAC_PROBES = {
    "uname -a": MAC_UNAME,
    "node -v": "v22.11.0",
    "printenv TZ": "Europe/London",
    "printenv NODE_OPTIONS": "--max-old-space-size=4096",
    "stat -f -c %T .": "",
    "diskutil info /": "",
    "sha256sum package-lock.json": "aaa111  package-lock.json",
    "env": MAC_ENV,
}
LINUX_PROBES = {
    "uname -a": LINUX_UNAME,
    "node -v": "v18.20.4",
    "printenv TZ": "UTC",
    "printenv NODE_OPTIONS": "--max-old-space-size=2048",
    "stat -f -c %T .": "",
    "diskutil info /": "",
    "sha256sum package-lock.json": "aaa111  package-lock.json",
    "env": LINUX_ENV,
}
RAW_PII = (
    "alice@example.com",
    "bob@example.org",
    "/Users/alice",
    "/home/bob",
    "alices-mac",
    "bob-staging",
    "10.20.30.40",
    "192.168.1.20",
    "00:1b:44:11:3a:b7",
    "00-1b-44-11-3a-b8",
    "2001:db8::5",
    "horse battery",
    "hunter2",
)


def _write_bundles(folder: Path) -> None:
    for name, env, uname in (("alice", MAC_ENV, MAC_UNAME), ("bob", LINUX_ENV, LINUX_UNAME)):
        data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
        data["commands"]["env"]["stdout"] = env
        data["commands"]["uname -a"]["stdout"] = uname
        (folder / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


def test_macos_bundle_is_masked_by_parse_fingerprint() -> None:
    fp = parse_fingerprint("alice", MAC_PROBES)
    dumped = json.dumps(fp).lower()
    for raw in (
        "alice@example.com",
        "/users/alice",
        "alices-mac",
        "10.20.30.40",
        "00:1b:44:11:3a:b7",
        "2001:db8::5",
        "horse battery",
        "hunter2",
    ):
        assert raw not in dumped
    assert fp["os"] == "Darwin"
    assert fp["env"]["HOME"] == "/Users/[redacted:user]"
    assert fp["env"]["USER"] == "[redacted:user]"
    assert fp["env"]["HOSTNAME"] == "[redacted:host]"
    assert fp["env"]["EMAIL"] == "[redacted:email]"
    assert fp["env"]["IFACE_MAC"] == "[redacted:mac]"
    assert fp["env"]["DB_PASSWORD"] == "[redacted]"
    assert fp["env"]["TZ"] == "Europe/London"


def test_linux_bundle_is_masked_by_parse_fingerprint() -> None:
    fp = parse_fingerprint("bob", LINUX_PROBES)
    dumped = json.dumps(fp).lower()
    for raw in ("bob@example.org", "/home/bob", "bob-staging", "192.168.1.20", "horse battery"):
        assert raw.lower() not in dumped
    assert fp["os"] == "Linux"
    assert fp["env"]["HOME"] == "/home/[redacted:user]"
    assert fp["env"]["IFACE_MAC"] == "[redacted:mac]"
    assert fp["env"]["SSH_CLIENT"] == "[redacted:ip] 40022 22"


def test_the_diff_still_finds_the_four_real_suspects_after_masking() -> None:
    alice = parse_fingerprint("alice", MAC_PROBES)
    bob = parse_fingerprint("bob", LINUX_PROBES)
    assert [s.name for s in diff_fingerprints(alice, bob)] == ["tz", "node", "node_options", "os"]


async def test_the_case_runs_on_masked_bundles_and_nothing_personal_is_written(
    tmp_path: Path,
) -> None:
    _write_bundles(tmp_path)
    receipt, room = await run_offline(tmp_path)
    doc = "\n".join(room.documents.values())
    transcript = "\n".join(text for _, text in room.messages)
    written = (json.dumps(receipt) + doc + transcript).lower()

    for raw in RAW_PII:
        assert raw.lower() not in written
    assert [s["name"] for s in receipt["suspects"]] == [
        "tz",
        "node",
        "node_options",
        "fs_case",
        "os",
    ]
    assert receipt["culprit"]["variable"] == "node"
    assert receipt["fix"]["outcome"] == "pass"
    assert '"DB_PASSWORD": "[redacted]"' in doc
    assert "[redacted:email]" in doc
    assert "[redacted:user]" in doc
    assert receipt["redactions"] >= 10
