"""Secret formats and secret words: each positive is masked, each negative is left alone.

The token bodies are built at run time so no literal in this file looks like a live credential.
"""

import pytest

from bailiff.redact import MARKER, mask_secret_lines, redact

GITHUB_PAT = "github_" + "pat_" + "A1b2C3d4E5f6G7h8I9j0K1"
SLACK_BOT = "xox" + "b-1234567890-abcdefghij"
AWS_TEMP = "ASIA" + "ABCDEFGH23456789"
GOOGLE_KEY = "AI" + "za" + "a" * 35
NPM_TOKEN = "npm" + "_" + "a" * 36

REDACT_CASES = [
    (GITHUB_PAT, MARKER, 1),
    (SLACK_BOT, MARKER, 1),
    (AWS_TEMP, MARKER, 1),
    (GOOGLE_KEY, MARKER, 1),
    (NPM_TOKEN, MARKER, 1),
    (f"id={AWS_TEMP} x", f"id={MARKER} x", 1),
    ("github_pat_short", "github_pat_short", 0),
    ("xoxq-1234567890-abcdefghij", "xoxq-1234567890-abcdefghij", 0),
    ("ASIAabcdefgh23456789", "ASIAabcdefgh23456789", 0),
    ("AI" + "za" + "a" * 29, "AI" + "za" + "a" * 29, 0),
    ("npm_" + "a" * 19, "npm_" + "a" * 19, 0),
    ("curl -u alice:pw123 https://x", f"curl -u {MARKER} https://x", 1),
    ("curl --user alice:pw123 https://x", f"curl --user {MARKER} https://x", 1),
    ('curl -u "alice:pw 123" x', f"curl -u {MARKER} x", 1),
    ("curl https://x", "curl https://x", 0),
    ("password:\u00a0hunter2", f"password:\u00a0{MARKER}", 1),
    ("password\uff1ahunter2", f"password\uff1a{MARKER}", 1),
    ("password is hunter2 here", "password is hunter2 here", 0),
    ("['--password', 'x']", f"['--password', '{MARKER}']", 1),
    ('["--token", "abc"]', f'["--token", "{MARKER}"]', 1),
    ("['--verbose', 'x']", "['--verbose', 'x']", 0),
]


@pytest.mark.parametrize(("text", "expected", "hits"), REDACT_CASES)
def test_a_new_secret_format_or_flag_is_masked_and_a_lookalike_is_not(
    text: str, expected: str, hits: int
) -> None:
    assert redact(text) == (expected, hits)


LINE_CASES = [
    ("passphrase=hunter2", f"passphrase={MARKER}", 1),
    ("accountkey=abc def", f"accountkey={MARKER}", 1),
    ("sessionid=abc", f"sessionid={MARKER}", 1),
    ("session_id=abc", f"session_id={MARKER}", 1),
    ("DB_PASS=abc", f"DB_PASS={MARKER}", 1),
    ("pass=hunter2", "pass=hunter2", 0),
    ("bypass=1", "bypass=1", 0),
    ("SESSION=abc", "SESSION=abc", 0),
    ("DB_HOST=db1", "DB_HOST=db1", 0),
    ("PWD=/srv/app", "PWD=/srv/app", 0),
]


@pytest.mark.parametrize(("text", "expected", "hits"), LINE_CASES)
def test_a_new_secret_word_masks_its_line_value_and_a_lookalike_key_does_not(
    text: str, expected: str, hits: int
) -> None:
    assert mask_secret_lines(text) == (expected, hits)
