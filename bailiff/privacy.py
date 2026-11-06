"""What the room transcript shows of the masking: placeholder counts and one example line.

The offline demo prints these and the receipt carries them, so both read the transcript one way.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from typing import Any

from bailiff.redact import mask_secret_lines, redact

_PLACEHOLDER = re.compile(r"\[redacted(?::(\w{1,32}))?\]")
_TYPED = re.compile(r"\[redacted:\w{1,32}\]")
EXAMPLE_CHARS = 100
_LEAD = 30


def placeholder_counts(messages: Sequence[tuple[str, str]]) -> dict[str, int]:
    """How many placeholders of each type the transcript holds. A bare marker counts as secret."""
    counts: Counter[str] = Counter()
    for _, text in messages:
        counts.update(match.group(1) or "secret" for match in _PLACEHOLDER.finditer(text))
    return dict(sorted(counts.items()))


def masked_example(messages: Sequence[tuple[str, str]]) -> str | None:
    """A window of at most EXAMPLE_CHARS from the first transcript line with a typed placeholder,
    or failing that any placeholder. The window starts a little before the placeholder. A window
    that masking would still change (a cut that strips a cue such as `v` or `==`) is skipped, so
    the example always validates."""
    for pattern in (_TYPED, _PLACEHOLDER):
        for _, text in messages:
            for line in text.splitlines():
                for found in pattern.finditer(line):
                    start = max(0, found.start() - _LEAD)
                    window = line[start : start + EXAMPLE_CHARS]
                    if not redact(window)[1] and not mask_secret_lines(window)[1]:
                        return window
    return None


def privacy_record(messages: Sequence[tuple[str, str]]) -> dict[str, Any] | None:
    """The receipt's `privacy` object, or None when the transcript holds no placeholder."""
    counts = placeholder_counts(messages)
    example = masked_example(messages)
    if not counts or example is None:
        return None
    return {"placeholders": counts, "example": example}
