import pytest

from bailiff.redact import MARKER, mask_secret_lines

LINE_CASES = [
    ("DB_PASSWORD=correct horse battery", f"DB_PASSWORD={MARKER}", 1),
    ("export API_TOKEN=abc def", f"export API_TOKEN={MARKER}", 1),
    ("api_key=a;b&c,d", f"api_key={MARKER}", 1),
    ("password=Hunter2", f"password={MARKER}", 1),
    ("SECRET=", f"SECRET={MARKER}", 1),
    ("TOKEN=abc\r\nTZ=UTC", f"TOKEN={MARKER}\r\nTZ=UTC", 1),
    ("A=1\nTOKEN=x y\nB=2", f"A=1\nTOKEN={MARKER}\nB=2", 1),
    ("PWD=/home/bob", "PWD=/home/bob", 0),
    ("ENV=prod DB_PASSWORD=hunter2 tail", "ENV=prod DB_PASSWORD=hunter2 tail", 0),
    ("Authorization: Basic dXNl=", "Authorization: Basic dXNl=", 0),
    ("echo TOKEN=abc def", "echo TOKEN=abc def", 0),
    ("no equals here", "no equals here", 0),
    ("", "", 0),
]


@pytest.mark.parametrize(("text", "expected", "hits"), LINE_CASES)
def test_a_secret_named_line_loses_its_whole_value(text: str, expected: str, hits: int) -> None:
    assert mask_secret_lines(text) == (expected, hits)


def test_the_tail_of_a_secret_line_is_gone_not_just_the_first_word() -> None:
    assert mask_secret_lines("DB_PASSWORD=correct horse battery") == (
        "DB_PASSWORD=[redacted]",
        1,
    )


def test_a_secret_line_inside_a_json_envelope_is_masked_to_the_escaped_newline() -> None:
    text = r'{"stdout": "DB_PASSWORD=correct horse battery\nTZ=UTC\n", "exit_code": 0}'
    assert mask_secret_lines(text) == (
        r'{"stdout": "DB_PASSWORD=[redacted]\nTZ=UTC\n", "exit_code": 0}',
        1,
    )


def test_masking_secret_lines_twice_changes_nothing_the_second_time() -> None:
    once, _ = mask_secret_lines("A=1\nTOKEN=x y\nDB_PASSWORD=z")
    assert mask_secret_lines(once) == (once, 0)
