_ALLOWED: frozenset[tuple[str, ...]] = frozenset(
    {
        ("uname", "-a"),
        ("node", "-v"),
        ("git", "config", "core.ignorecase"),
        ("printenv", "TZ"),
        ("printenv", "NODE_OPTIONS"),
        ("stat", "-f", "-c", "%T", "."),
        ("diskutil", "info", "/"),
        ("sha256sum", "package-lock.json"),
        ("env",),
        ("node", "test.js"),
        ("/opt/node22/bin/node", "test.js"),
    }
)

ENV_OVERLAY_KEYS = frozenset({"TZ", "NODE_OPTIONS"})


def is_allowed(cmd: object) -> bool:
    if not isinstance(cmd, list) or not all(isinstance(part, str) for part in cmd):
        return False
    return tuple(cmd) in _ALLOWED


def is_allowed_overlay(env: dict[str, str]) -> bool:
    return set(env) <= ENV_OVERLAY_KEYS
