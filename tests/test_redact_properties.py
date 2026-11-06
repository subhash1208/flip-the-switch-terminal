import time

from hypothesis import given, settings
from hypothesis import strategies as st

from bailiff.fingerprint import parse_fingerprint
from bailiff.redact import MARKER, redact

FAST = settings(deadline=None, max_examples=200)

SECRET_KEYS = st.from_regex(
    r"[A-Z]{1,6}_(SECRET|TOKEN|PASSWORD|AUTH|API_KEY)_[A-Z]{1,6}", fullmatch=True
)
VALUES = st.text(alphabet=st.characters(exclude_categories=("Cc", "Cs", "Zl", "Zp")), max_size=60)
FRAGMENTS = st.sampled_from(
    [
        "TOKEN=",
        "DB_PASSWORD=",
        "--password ",
        "api_key: ",
        '"secret": "',
        "Cookie: ",
        "Authorization: Basic ",
        "Bearer ",
        "a=",
        "https://u:",
        "@",
        " ",
        ";",
        "&",
        ",",
        "'",
        '"',
        "\\",
        "\n",
        "x",
        MARKER,
        "sk_live_" + "a" * 16,
        "[truncated 3 chars]",
    ]
)
TEXT = st.one_of(st.text(max_size=400), st.lists(FRAGMENTS, max_size=60).map("".join))
LINES = st.one_of(st.text(max_size=5000), st.lists(FRAGMENTS, max_size=200).map("".join))


@FAST
@given(TEXT)
def test_redact_never_raises_on_arbitrary_text(text: str) -> None:
    out, hits = redact(text)
    assert isinstance(out, str)
    assert hits >= 0


@FAST
@given(TEXT)
def test_redaction_is_idempotent(text: str) -> None:
    assert redact(redact(text)[0])[0] == redact(text)[0]


@FAST
@given(TEXT)
def test_output_length_is_bounded_by_input_and_hit_count(text: str) -> None:
    out, hits = redact(text)
    assert len(out) <= len(text) + 40 + 24 * hits


@FAST
@given(SECRET_KEYS, VALUES)
def test_a_secret_value_leaves_no_run_of_four_characters_in_the_fingerprint(
    key: str, value: str
) -> None:
    env = parse_fingerprint("m", {"env": f"{key}={value}"})["env"]
    visible = env[key].replace(MARKER, "")
    for size in range(4, len(value) + 1):
        for start in range(len(value) - size + 1):
            assert value[start : start + size] not in visible


@FAST
@given(SECRET_KEYS, VALUES)
def test_the_key_stays_visible_after_redaction(key: str, value: str) -> None:
    assert redact(f"{key}={value}")[0].startswith(f"{key}=")
    assert key in parse_fingerprint("m", {"env": f"{key}={value}"})["env"]


@FAST
@given(LINES)
def test_a_generated_line_of_up_to_5k_characters_redacts_in_under_a_second(line: str) -> None:
    started = time.perf_counter()
    redact(line)
    assert time.perf_counter() - started < 1.0
