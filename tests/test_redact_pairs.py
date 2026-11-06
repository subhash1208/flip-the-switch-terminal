import pytest

from bailiff.redact import MARKER, redact


def test_a_secret_after_a_non_secret_pair_on_the_same_line_is_still_masked() -> None:
    assert redact("ENV=prod DB_PASSWORD=hunter2 tail") == (f"ENV=prod DB_PASSWORD={MARKER} tail", 1)


def test_a_secret_inside_a_json_envelope_is_masked_without_breaking_the_secret_free_keys() -> None:
    text = r'{"stdout": "HOME=/Users/alice\nDATABASE_PASSWORD=hunter2-alice\n", "exit_code": 0}'
    out, count = redact(text)
    assert "hunter2" not in out
    assert "HOME=/Users/alice" in out
    assert '"exit_code": 0}' in out
    assert count == 1


PAIR_CASES = [
    ("x?a=1&token=abc123", "x?a=1&token=[redacted]", 1),
    ("A=1;TOKEN=abc123", "A=1;TOKEN=[redacted]", 1),
    ("JAVA_OPTS=-Dpassword=hunter2", "JAVA_OPTS=-Dpassword=[redacted]", 1),
    ("NODE_OPTIONS=--token=abc123", "NODE_OPTIONS=--token=[redacted]", 1),
    (
        '{"api_key": "abc123", "password":"zz"}',
        '{"api_key": "[redacted]", "password":"[redacted]"}',
        2,
    ),
    ("password = hunter2", "password = [redacted]", 1),
    ("TOKEN=abc\\def", "TOKEN=[redacted]", 1),
    ('password="a b" next=1', "password=[redacted] next=1", 1),
    ('TOKEN="abc def', "TOKEN=[redacted]", 1),
    ("Authorization=Bearer abc.def", "Authorization=[redacted] [redacted]", 2),
]


@pytest.mark.parametrize(("text", "expected", "count"), PAIR_CASES)
def test_a_secret_joined_to_a_non_secret_value_is_masked(
    text: str, expected: str, count: int
) -> None:
    out, hits = redact(text)
    assert out == expected
    assert hits == count
    assert redact(out) == (out, 0)


@pytest.mark.parametrize("text", ["HOME=/Users/alice&LANG=en", '{"stdout": "exit 0"}'])
def test_pairs_without_a_secret_key_are_left_alone(text: str) -> None:
    assert redact(text) == (text, 0)


def test_a_quoted_secret_value_is_masked_as_one_value() -> None:
    out, count = redact('password="correct horse" next=1')
    assert out == f"password={MARKER} next=1"
    assert count == 1
