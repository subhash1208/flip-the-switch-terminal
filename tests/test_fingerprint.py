import pytest

from bailiff.fingerprint import diff_fingerprints, parse_fingerprint
from bailiff.models import Suspect

MAC_PROBES = {
    "uname -a": "Darwin alices-mac.local 24.1.0 Darwin Kernel Version 24.1.0 arm64",
    "node -v": "v22.11.0",
    "printenv TZ": "Asia/Kolkata",
    "printenv NODE_OPTIONS": "",
    "stat -f -c %T .": "",
    "diskutil info /": "   File System Personality:  APFS\n   Type (Bundle):  apfs\n",
    "sha256sum package-lock.json": "aaa111  package-lock.json",
    "env": "HOME=/Users/alice\nDATABASE_PASSWORD=hunter2\n",
}

LINUX_PROBES = {
    "uname -a": "Linux bob-staging 6.8.0-45-generic #45-Ubuntu SMP x86_64 GNU/Linux",
    "node -v": "v18.20.4",
    "printenv TZ": "UTC",
    "printenv NODE_OPTIONS": "--openssl-legacy-provider",
    "stat -f -c %T .": "ext2/ext3",
    "diskutil info /": "",
    "sha256sum package-lock.json": "bbb222  package-lock.json",
    "env": "HOME=/home/bob\n",
}


def test_parses_macos_probes_and_redacts_env() -> None:
    fp = parse_fingerprint("alice", MAC_PROBES)
    assert fp["machine"] == "alice"
    assert fp["os"] == "Darwin"
    assert fp["node"] == "v22.11.0"
    assert fp["tz"] == "Asia/Kolkata"
    assert fp["node_options"] is None
    assert fp["fs_case"] == "case-insensitive"
    assert fp["lock_sha"] == "aaa111"
    assert fp["env"] == {"HOME": "/Users/alice", "DATABASE_PASSWORD": "[redacted]"}


def test_parses_linux_probes_as_case_sensitive_ext4() -> None:
    fp = parse_fingerprint("bob", LINUX_PROBES)
    assert fp["os"] == "Linux"
    assert fp["node_options"] == "--openssl-legacy-provider"
    assert fp["fs_case"] == "case-sensitive"


def test_missing_probes_are_tolerated() -> None:
    assert parse_fingerprint("ci", {}) == {
        "machine": "ci",
        "os": "",
        "node": "",
        "tz": "",
        "node_options": None,
        "fs_case": "unknown",
        "lock_sha": "",
        "env": {},
    }


@pytest.mark.parametrize(
    ("stat_out", "diskutil_out", "expected"),
    [
        ("ext2/ext3", "", "case-sensitive"),
        ("xfs", "", "case-sensitive"),
        ("overlayfs", "", "case-sensitive"),
        ("msdos", "", "case-insensitive"),
        ("", "File System Personality: APFS", "case-insensitive"),
        ("", "File System Personality: Case-sensitive APFS", "case-sensitive"),
        ("", "Type: hfs (non-case-sensitive)", "case-insensitive"),
        ("", "", "unknown"),
    ],
)
def test_detects_filesystem_case_sensitivity(
    stat_out: str, diskutil_out: str, expected: str
) -> None:
    probes = {"stat -f -c %T .": stat_out, "diskutil info /": diskutil_out}
    assert parse_fingerprint("m", probes)["fs_case"] == expected


def test_diff_lists_differing_fields_in_fixed_order() -> None:
    alice = parse_fingerprint("alice", MAC_PROBES)
    bob = parse_fingerprint("bob", LINUX_PROBES)
    suspects = diff_fingerprints(alice, bob)
    assert [s.name for s in suspects] == [
        "tz",
        "node",
        "node_options",
        "fs_case",
        "os",
        "lock_sha",
    ]
    assert suspects[0] == Suspect("tz", "Asia/Kolkata", "UTC", "unknown")
    assert suspects[-1] == Suspect("lock_sha", "aaa111", "bbb222", "unknown")


def test_identical_fingerprints_yield_no_suspects() -> None:
    same = parse_fingerprint("bob", MAC_PROBES)
    assert diff_fingerprints(parse_fingerprint("alice", MAC_PROBES), same) == []
