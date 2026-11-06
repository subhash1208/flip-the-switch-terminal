import re
from collections.abc import Callable
from typing import Any

from bailiff.models import Suspect
from bailiff.redact import mask_bounded

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


def _compared(probe: Callable[[str], str]) -> dict[str, Any]:
    return {
        "os": _first_token(probe("uname -a")),
        "node": probe("node -v"),
        "tz": probe("printenv TZ"),
        "node_options": probe("printenv NODE_OPTIONS") or None,
        "fs_case": _fs_case(probe("stat -f -c %T ."), probe("diskutil info /")),
        "lock_sha": _first_token(
            probe("sha256sum package-lock.json") or probe("shasum -a 256 package-lock.json")
        ),
    }


def parse_fingerprint(machine: str, probes: dict[str, str]) -> dict[str, Any]:
    def shown(command: str) -> str:
        # Display values only. Each is capped, then masked, so a fingerprint stays clean when a
        # caller skips agent._probe. A secret-named line is masked whole first: a space, `;`, `&`,
        # `,` or quote in its value would otherwise leave the tail visible.
        return mask_bounded(probes.get(command) or "")[0].strip()

    return {"machine": machine, **_compared(shown), "env": _parse_env(shown("env"))}


def raw_compared(probes: dict[str, str]) -> dict[str, Any]:
    """The compared fields from the unmasked probe output. Equality is decided on these, so two
    values that differ only in what masking hides are still a suspect. Keep these in memory."""
    return _compared(lambda command: (probes.get(command) or "").strip())


def diff_fingerprints(
    a: dict[str, Any],
    b: dict[str, Any],
    raw_a: dict[str, Any] | None = None,
    raw_b: dict[str, Any] | None = None,
) -> list[Suspect]:
    """A field is a suspect when its raw values differ (raw_a, raw_b when given, else the
    fingerprints themselves). The suspect shows the masked values."""
    left = raw_a if raw_a is not None else a
    right = raw_b if raw_b is not None else b
    suspects: list[Suspect] = []
    for field in _COMPARED_FIELDS:
        if str(left.get(field) or "") != str(right.get(field) or ""):
            alice = str(a.get(field) or "")
            bob = str(b.get(field) or "")
            suspects.append(Suspect(name=field, alice=alice, bob=bob, verdict="unknown"))
    return suspects
