import re
from collections.abc import Callable

MARKER = "[redacted]"
_MAX_PASSES = 5

_SECRET_WORDS = r"secret|token|password|passwd|api[_-]?key|private[_-]?key|credential|auth"
_KEY = r"[-A-Za-z0-9_.]"
_QUOTED = r"\"[^\"\r\n]*\"?|'[^'\r\n]*'?"
# An unquoted value ends at whitespace, a quote, or a `&`, `;` or `,` separator. A backslash ends
# it only before an escape letter, so `abc\def` is masked whole.
_PLAIN = r"(?:[^\s\"'\\&;,]|\\(?![ntr\"']))*"
# Only a secret key consumes its value. A non-secret pair is passed over, so a secret pair inside
# its value (`JAVA_OPTS=-Dpassword=x`) is still found by the scan.
_KEY_VALUE = re.compile(
    rf"(?<!{_KEY})(?={_KEY}*(?:{_SECRET_WORDS}){_KEY}*[ \t]*=)"
    rf"({_KEY}+[ \t]*=[ \t]*)({_QUOTED}|{_PLAIN})",
    re.IGNORECASE,
)
_JSON_KEY_VALUE = re.compile(
    rf"(\"{_KEY}*(?:{_SECRET_WORDS}){_KEY}*\"[ \t]*:[ \t]*)(\"[^\"\r\n]*\")", re.IGNORECASE
)
_BEARER = re.compile(r"(\bBearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)
_URL_CREDENTIALS = re.compile(
    r"((?<![A-Za-z0-9+.\-])[a-z][a-z0-9+.\-]*://[^\s/:@]+:)[^\s/@]+@", re.IGNORECASE
)
_TOKENS = (
    re.compile(r"\bsk[-_][A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*"),
)

Rule = tuple[re.Pattern[str], Callable[[re.Match[str]], str]]


def _mask_value(match: re.Match[str]) -> str:
    return f"{match.group(1)}{MARKER}"


def _mask_json_value(match: re.Match[str]) -> str:
    return f'{match.group(1)}"{MARKER}"'


def _mask_all(match: re.Match[str]) -> str:
    return MARKER


def _bearer(match: re.Match[str]) -> str:
    return f"{match.group(1)}{MARKER}"


def _url(match: re.Match[str]) -> str:
    return f"{match.group(1)}{MARKER}@"


_RULES: tuple[Rule, ...] = (
    (_BEARER, _bearer),
    (_JSON_KEY_VALUE, _mask_json_value),
    (_KEY_VALUE, _mask_value),
    (_URL_CREDENTIALS, _url),
    *((token, _mask_all) for token in _TOKENS),
)


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


def redact(text: str) -> tuple[str, int]:
    if not isinstance(text, str):
        text = str(text)
    total = 0
    for _ in range(_MAX_PASSES):
        changed = 0
        for pattern, repl in _RULES:
            text, hits = _sub(pattern, text, repl)
            changed += hits
        total += changed
        if changed == 0:
            break
    return text, total
