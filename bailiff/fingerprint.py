import re
from typing import Any

from bailiff.models import Suspect
from bailiff.redact import redact

_SENSITIVE_RE = re.compile(r"(?<!non-)case-sensitive")
_INSENSITIVE_HINTS = (
    "case-insensitive",
    "non-case-sensitive",
    "apfs",
    "hfs",
    "vfat",
    "msdos",
    "exfat",
    "ntfs",
)
_SENSITIVE_HINTS = ("ext2", "ext3", "ext4", "xfs", "btrfs", "overlay")
_COMPARED_FIELDS = ("tz", "node", "node_options", "fs_case", "os", "lock_sha")


def _first_token(text: str) -> str:
    parts = text.split()
    return parts[0] if parts else ""


def _fs_case(stat_out: str, diskutil_out: str) -> str:
    text = f"{stat_out} {diskutil_out}".lower()
    if _SENSITIVE_RE.search(text):
        return "case-sensitive"
    if any(hint in text for hint in _INSENSITIVE_HINTS):
        return "case-insensitive"
    if any(hint in text for hint in _SENSITIVE_HINTS):
        return "case-sensitive"
    return "unknown"


def _parse_env(text: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep and key:
            env[key] = value
    return env


def parse_fingerprint(machine: str, probes: dict[str, str]) -> dict[str, Any]:
    def probe(command: str) -> str:
        return (probes.get(command) or "").strip()

    env_text, _ = redact(probe("env"))
    return {
        "machine": machine,
        "os": _first_token(probe("uname -a")),
        "node": probe("node -v"),
        "tz": probe("printenv TZ"),
        "node_options": probe("printenv NODE_OPTIONS") or None,
        "fs_case": _fs_case(probe("stat -f -c %T ."), probe("diskutil info /")),
        "lock_sha": _first_token(probe("sha256sum package-lock.json")),
        "env": _parse_env(env_text),
    }


def diff_fingerprints(a: dict[str, Any], b: dict[str, Any]) -> list[Suspect]:
    suspects: list[Suspect] = []
    for field in _COMPARED_FIELDS:
        alice = str(a.get(field) or "")
        bob = str(b.get(field) or "")
        if alice != bob:
            suspects.append(Suspect(name=field, alice=alice, bob=bob, verdict="unknown"))
    return suspects
