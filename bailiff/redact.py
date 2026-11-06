"""Masking of secrets and personal data before text leaves the Bailiff: room posts, the case file
and the receipt.

Best-effort, not a guarantee. `redact()` runs its rules for a few passes. `mask_secret_lines()`
masks the whole value of a line whose key is secret-named. `redact_bounded()` and `mask_bounded()`
cap the input at MAX_REDACT_CHARS first and say how many characters they dropped.

Versions and IPv4: a dotted quad is left alone only when a `v` is attached in front (`v1.2.3.4`),
`==` sits directly before it (`pkg==1.2.3.4`), or a pre-release or build tag follows it
(`1.2.3.4-rc1`, `-alpha`, `-beta`, `-pre`, `-dev`, `-snapshot`, `+build`). Every other neighbour,
such as `@`, `-`, `node`, `version` or a space, leaves it masked, so `root@10.0.0.5`, `- 10.0.0.5`
and `10.0.0.5-eth0` are all masked. Privacy wins: `version 1.2.3.4` is masked as a false positive
by design.

A secret word anywhere in a line's key is a secret: `auth: 4 passed` becomes
`auth: [redacted] passed`. That is a false positive by design, and no rule is weakened to avoid it.

Known limits, not covered by any rule (the list is not exhaustive):
- `docker login -p X` and `mysql -pX`: a short flag with its value attached is not masked.
- A multi-line secret (a PEM key body) is masked on its first line only; later lines are not.
- YAML block scalars (`key: |`) that hold a secret are not masked.
- Unquoted numeric JSON secrets (`"token": 12345`) are not masked.
- A quoted value holding an unescaped copy of its own quote leaves a fragment after the mask.
- Bare national phone numbers, with no `+` country code, are not masked.
- Free-text names outside a home path or an identity line are not masked.
- Dash-separated hostnames such as `ip-10-0-1-5` are not masked.
- Inline `KEY=value tail` in the middle of a sentence: a space ends the value, so `tail` stays.
- Spaced international phones (`+44 20 7946 0958`) are not masked: only a `+` directly followed by
  digits is.
- A UNC share path (a server name after two leading backslashes) and `/root` are not masked: only
  the Windows `Users` and the POSIX `/home/` and `/Users/` homes are.
- A space-separated SSN (`123 45 6789`) is not masked: only a dashed one is.
- IBAN, Aadhaar and dates of birth are not covered.
- A tag after an address keeps it: `10.0.0.5+eth0` and `10.0.0.5-dev1` survive, by the tag rule.

Decisions, not rules:
- `PWD` is not a secret word: it is the working-directory variable, so `PWD=/srv/app` stays a path.
- `pass` is not a secret word: it matches `bypass`.
- `-u` and `--user` mask the value after them, so `sort -u file` loses `file`. That false positive
  is accepted, as the other secret words accept theirs.
"""

import re
from collections.abc import Callable
from functools import partial
from ipaddress import IPv4Address, IPv6Address

MARKER = "[redacted]"
MAX_REDACT_CHARS = 65536
_MAX_PASSES = 5

# The one list of secret-name words. scripted/runner.py builds its env filter from it too.
SECRET_WORDS = (
    "secret",
    "token",
    "password",
    "passwd",
    "api[_-]?key",
    "private[_-]?key",
    "credential",
    "auth",
    "passphrase",
    "accountkey",
    "session[_-]?id",
    "db[_-]?pass",
)
SECRET_KEY = re.compile("|".join(SECRET_WORDS), re.IGNORECASE)
_KEY = r"[-A-Za-z0-9_.]"
_QUOTED = r"\"[^\"\r\n]*\"?|'[^'\r\n]*'?"
# An unquoted value ends at whitespace, a quote, or a `&`, `;` or `,` separator. A backslash ends
# it only before an escape letter, so `abc\def` is masked whole.
_PLAIN = r"(?:[^\s\"'\\&;,]|\\(?![ntr\"']))*"
_VALUE = re.compile(rf"{_QUOTED}|{_PLAIN}")
# `key=value`, `key: value` or `--flag value`. The key is one maximal run of key characters, so
# the scan is linear. Only a secret key consumes its value (see _mask_assignments). A no-break
# space counts as a space, and a full-width colon as a colon.
_ASSIGN = re.compile(
    rf"(?<!{_KEY})(?P<dashes>--)?(?P<key>{_KEY}+)"
    r"(?P<sep>[ \t\u00a0]*[=:\uff1a][ \t\u00a0]*|[ \t\u00a0]+)"
)
# A JSON or Python-repr pair: the key and the value may each use either quote, and the value
# honours backslash escapes (`"p\"tail"` is one value). Each start scans one value, so it is linear.
_JSON_PAIR = re.compile(
    rf"(?P<kq>[\"'])(?P<key>{_KEY}+)(?P=kq)(?P<sep>[ \t]*:[ \t]*)"
    rf"(?P<vq>[\"'])(?P<value>(?:\\.|(?!(?P=vq))[^\r\n\\])*)(?P=vq)"
)
# An argv list repr such as `['--password', 'x']`: a secret `--` flag, then a quoted element.
_ARGV_PAIR = re.compile(
    rf"(?P<flag>(?P<fq>[\"'])--[-\w]*?(?:{SECRET_KEY.pattern})[-\w]*(?P=fq))"
    r"(?P<sep>[ \t]*,[ \t]*)(?P<vq>[\"'])(?P<value>(?:\\.|(?!(?P=vq))[^\r\n\\])*)(?P=vq)",
    re.IGNORECASE,
)
_HEADER = re.compile(
    r"(?<![\w-])((?:proxy-)?authorization|set-cookie|cookie|x-api-key|x-auth-token)"
    r"([ \t]*:[ \t]*)([^\r\n]*)",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(\bBearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)
# `curl -u user:pw` and `--user user:pw`: the value after the flag, quoted or up to whitespace.
_CURL_USER = re.compile(rf"((?<![\w-])(?:-u|--user)[ \t]+)(?:{_QUOTED}|\S+)")
# `scheme://user:password@host`. The user may be empty. The password may hold `/` and may run to
# the last `@` before the next whitespace or `://`, so each start scans one segment only.
_URL_CREDENTIALS = re.compile(
    r"((?<![A-Za-z0-9+.\-])[a-z][a-z0-9+.\-]*://[^\s/:@]*:)(?:(?!://)\S)+@", re.IGNORECASE
)
_TOKENS = (
    re.compile(r"\bsk[-_][A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"\bnpm_[A-Za-z0-9]{20,}"),
)


def _mask_json_pair(match: re.Match[str]) -> str:
    if match.group("value") == MARKER or not SECRET_KEY.search(match.group("key")):
        return match.group(0)
    kq, vq = match.group("kq"), match.group("vq")
    return f"{kq}{match.group('key')}{kq}{match.group('sep')}{vq}{MARKER}{vq}"


def _argv_value(match: re.Match[str]) -> str:
    if match.group("value") == MARKER:
        return match.group(0)
    vq = match.group("vq")
    return f"{match.group('flag')}{match.group('sep')}{vq}{MARKER}{vq}"


def _mask_header(match: re.Match[str]) -> str:
    if match.group(3) == MARKER:
        return match.group(0)
    return f"{match.group(1)}{match.group(2)}{MARKER}"


def _mask_all(match: re.Match[str]) -> str:
    return MARKER


def _bearer(match: re.Match[str]) -> str:
    return f"{match.group(1)}{MARKER}"


def _url(match: re.Match[str]) -> str:
    return f"{match.group(1)}{MARKER}@"


def _sub(
    pattern: re.Pattern[str], text: str, repl: Callable[[re.Match[str]], str]
) -> tuple[str, int]:
    hits = 0

    def apply(match: re.Match[str]) -> str:
        nonlocal hits
        out = repl(match)
        if out != match.group(0):
            hits += 1
        return out

    return pattern.sub(apply, text), hits


def _mask_assignments(text: str) -> tuple[str, int]:
    # Only a secret key consumes its value. A non-secret pair is passed over, so a secret pair
    # inside its value (`JAVA_OPTS=-Dpassword=x`) is still found.
    out: list[str] = []
    hits = 0
    emitted = 0
    pos = 0
    while (found := _ASSIGN.search(text, pos)) is not None:
        pos = found.end()
        spaced = found.group("sep").strip(" \t\u00a0") == ""
        if not SECRET_KEY.search(found.group("key")):
            continue
        if spaced and found.group("dashes") is None:
            continue
        value = _VALUE.match(text, pos)
        end = value.end() if value is not None else pos
        pos = end
        if text[found.end() : end] == MARKER:
            continue
        out.append(text[emitted : found.end()])
        out.append(MARKER)
        emitted = end
        hits += 1
    out.append(text[emitted:])
    return "".join(out), hits


_EMAIL = re.compile(
    r"(?<![\w.%+-])[\w.%+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){0,9}\.[A-Za-z]{2,24}"
    r"(?![\w-]|:[\w./~-])"
)


def _email(match: re.Match[str]) -> str:
    # `ssh://git@host/repo` names a git account, not a person.
    start = match.start()
    if match.group(0).startswith("git@") and match.string[max(0, start - 3) : start] == "://":
        return match.group(0)
    return "[redacted:email]"


_NAME = r"[^\\/:\"'<>|*?\s\[\]&;,=]"
_WIN_USER = rf"{_NAME}+(?: {_NAME}+){{0,2}}"
# A chain (`/Users/a/Users/a/...`) is one match: the lookbehind only guards the first segment, and
# the tail repeats segments with no lookbehind. Each segment is a separate name, so nothing backtracks.
_WIN_HOME = re.compile(
    rf"(?i)(?<!\w)([a-z]:[\\/]+users[\\/]+)({_WIN_USER})((?:[\\/]+users[\\/]+{_WIN_USER})*)"
)
_WIN_SEGMENT = re.compile(rf"(?i)([\\/]+users[\\/]+)({_WIN_USER})")
_POSIX_HOME = re.compile(rf"(?<![\w.-])(/(?:home|Users)/)({_NAME}+)((?:/(?:home|Users)/{_NAME}+)*)")
_POSIX_SEGMENT = re.compile(rf"(/(?:home|Users)/)({_NAME}+)")
_IDENTITY_KEYS = "USER|LOGNAME|USERNAME|HOSTNAME|COMPUTERNAME|HOST"
_IDENTITY_LINE = re.compile(
    rf"(?m)(?:^|(?<=\\n))([ \t]*(?:export[ \t]+)?)({_IDENTITY_KEYS})=[^\r\n\"\\]*"
)
_IDENTITY_INLINE = re.compile(rf"(?<![\w.-])({_IDENTITY_KEYS})=[^\s\"'\\&;,]+")
# The host is the token after the kernel name. A /proc/version line (`Linux version ...`) has none.
_UNAME_HOST = re.compile(
    r"(?:(?<![\w.-])|(?<=\\n))"
    r"((?:Linux|Darwin|FreeBSD|OpenBSD|NetBSD|SunOS|CYGWIN_NT\S*|MINGW\S*|MSYS\S*)[ \t]+)"
    r"(?!version[ \t])(\S+)(?=[ \t]+\d+(?:\.\d+)+)"
)
_MAC = re.compile(r"(?<![\w:-])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![\w:-])")
_IPV6 = re.compile(r"(?<![\w:.])[0-9A-Fa-f:]{2,39}(?![\w:.])")
_IPV4 = re.compile(
    r"(?<![\w.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\w|\.\d)"
)
_CARD = re.compile(r"(?<![\w-])\d(?:[ -]?\d){12,18}(?![\w-])")
_SSN = re.compile(r"(?<!\d)(?!000|666|9\d\d)\d{3}-\d{2}-\d{4}(?!\d)")
_PHONE = re.compile(r"(?<![\w+])\+[1-9]\d{6,14}(?!\d)")
_LONG_ID = re.compile(r"(?<![\w.])\d{15,19}(?![\w.])")
_TIME_KEY = re.compile(
    r"(?i)(?<![a-z])(?:[a-z]*_)?(?:(?:time|date|epoch|nanos|millis|ts)[a-z]*|at)"
    r"[\"']?[ \t]*[=:][ \t]*[\"']?$"
)
# A key never holds a backslash, so a start at a literal `\n` fails at once and every other
# start scans only its own segment. Without that, the scan was quadratic on `\n` runs.
_ASSIGN_LINE = re.compile(
    r'(?m)(?:^|(?<=\\n)|(?<=["]))([ \t]*(?:export[ \t]+)?)([^=\s"\\]+)=(?:(?!\\n)[^\r\n])*'
)
_HOST_KEYS = frozenset({"HOSTNAME", "COMPUTERNAME", "HOST"})
# Only a `v` attached in front, `==` directly before, or a pre-release or build tag after marks a
# version. A looser cue (`@`, `-`, `node`, `version`) would unmask a real address, so none is one.
# The tag must not run into a word: `10.0.0.5-devbox` is still an address.
_VERSION_CUE = re.compile(r"(?:\bv|==)$", re.IGNORECASE)
_VERSION_SUFFIX = re.compile(
    r"-(?:rc|alpha|beta|pre|dev|snapshot)(?:\d|(?![\w-]))|\+\w", re.IGNORECASE
)
_LOOPBACK = IPv4Address("127.0.0.1")
_SAFE_USER_DIRS = frozenset({"public", "default", "default user", "all users", "shared"})


def _placeholder(kind: str, match: re.Match[str]) -> str:
    return f"[redacted:{kind}]"


def _mask_user(prefix: str, name: str) -> str:
    if name.lower() in _SAFE_USER_DIRS:
        return f"{prefix}{name}"
    return f"{prefix}[redacted:user]"


def _win_home(match: re.Match[str]) -> str:
    tail = _WIN_SEGMENT.sub(lambda m: _mask_user(m.group(1), m.group(2)), match.group(3))
    return _mask_user(match.group(1), match.group(2)) + tail


def _posix_home(match: re.Match[str]) -> str:
    tail = _POSIX_SEGMENT.sub(lambda m: _mask_user(m.group(1), m.group(2)), match.group(3))
    return _mask_user(match.group(1), match.group(2)) + tail


def _identity_value(key: str) -> str:
    return "[redacted:host]" if key in _HOST_KEYS else "[redacted:user]"


def _identity_line(match: re.Match[str]) -> str:
    return f"{match.group(1)}{match.group(2)}={_identity_value(match.group(2))}"


def _identity_inline(match: re.Match[str]) -> str:
    return f"{match.group(1)}={_identity_value(match.group(1))}"


def _uname_host(match: re.Match[str]) -> str:
    return f"{match.group(1)}[redacted:host]"


def _is_version(match: re.Match[str]) -> bool:
    before = match.string[max(0, match.start() - 2) : match.start()]
    after = match.string[match.end() : match.end() + 16]
    return _VERSION_CUE.search(before) is not None or _VERSION_SUFFIX.match(after) is not None


def _ipv4(match: re.Match[str]) -> str:
    text = match.group(0)
    if _is_version(match):
        return text
    try:
        address = IPv4Address(text)
    except ValueError:
        return text
    return text if address.is_unspecified or address == _LOOPBACK else "[redacted:ip]"


def _ipv6(match: re.Match[str]) -> str:
    text = match.group(0)
    if text.count(":") < 2 or not any(ch.isdigit() for ch in text):
        return text
    try:
        address = IPv6Address(text)
    except ValueError:
        return text
    return text if address.is_loopback else "[redacted:ip]"


def _luhn(digits: str) -> bool:
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _timestamp_key(match: re.Match[str]) -> bool:
    start = match.start()
    return _TIME_KEY.search(match.string, max(0, start - 48), start) is not None


def _card(match: re.Match[str]) -> str:
    text = match.group(0)
    if not _luhn(text.replace(" ", "").replace("-", "")) or _timestamp_key(match):
        return text
    return "[redacted:card]"


def _long_id(match: re.Match[str]) -> str:
    return match.group(0) if _timestamp_key(match) else "[redacted:id]"


def _mask_line(match: re.Match[str]) -> str:
    key = match.group(2)
    if not SECRET_KEY.search(key):
        return match.group(0)
    return f"{match.group(1)}{key}={MARKER}"


def mask_secret_lines(text: str) -> tuple[str, int]:
    """Mask the whole value of any line whose key (the text before its first `=`) is secret."""
    return _sub(_ASSIGN_LINE, text, _mask_line)


Step = Callable[[str], tuple[str, int]]

_STEPS: tuple[Step, ...] = (
    partial(_sub, _HEADER, repl=_mask_header),
    partial(_sub, _BEARER, repl=_bearer),
    partial(_sub, _CURL_USER, repl=_bearer),
    partial(_sub, _JSON_PAIR, repl=_mask_json_pair),
    partial(_sub, _ARGV_PAIR, repl=_argv_value),
    partial(_sub, _URL_CREDENTIALS, repl=_url),
    _mask_assignments,
    *(partial(_sub, token, repl=_mask_all) for token in _TOKENS),
    partial(_sub, _EMAIL, repl=_email),
    partial(_sub, _WIN_HOME, repl=_win_home),
    partial(_sub, _POSIX_HOME, repl=_posix_home),
    partial(_sub, _IDENTITY_LINE, repl=_identity_line),
    partial(_sub, _IDENTITY_INLINE, repl=_identity_inline),
    partial(_sub, _UNAME_HOST, repl=_uname_host),
    partial(_sub, _MAC, repl=partial(_placeholder, "mac")),
    partial(_sub, _IPV6, repl=_ipv6),
    partial(_sub, _IPV4, repl=_ipv4),
    partial(_sub, _CARD, repl=_card),
    partial(_sub, _SSN, repl=partial(_placeholder, "ssn")),
    partial(_sub, _PHONE, repl=partial(_placeholder, "phone")),
    partial(_sub, _LONG_ID, repl=_long_id),
)


def redact(text: str) -> tuple[str, int]:
    if not isinstance(text, str):
        text = str(text)
    total = 0
    for _ in range(_MAX_PASSES):
        changed = 0
        for step in _STEPS:
            text, hits = step(text)
            changed += hits
        total += changed
        if changed == 0:
            break
    return text, total


def _cut(text: str) -> tuple[str, int]:
    """The first MAX_REDACT_CHARS of text, backed off to the last whitespace so no token is split.
    Returns the kept text and how many characters were dropped."""
    if len(text) <= MAX_REDACT_CHARS:
        return text, 0
    kept = text[:MAX_REDACT_CHARS]
    cut = max(kept.rfind(c) for c in " \t\r\n")
    if cut > 0:
        kept = kept[:cut]
    return kept, len(text) - len(kept)


def _marked(text: str, dropped: int) -> str:
    return f"{text}[truncated {dropped} chars]" if dropped else text


def redact_bounded(text: str) -> tuple[str, int]:
    """redact() over the first MAX_REDACT_CHARS only. The dropped count is shown in the marker."""
    kept, dropped = _cut(text)
    out, hits = redact(kept)
    return _marked(out, dropped), hits


def mask_bounded(text: str) -> tuple[str, int]:
    """mask_secret_lines() then redact(), over the first MAX_REDACT_CHARS only. The cap comes
    before the masking, so the bound holds for any text, whichever caller passes it."""
    kept, dropped = _cut(text)
    masked, line_hits = mask_secret_lines(kept)
    out, hits = redact(masked)
    return _marked(out, dropped), line_hits + hits
