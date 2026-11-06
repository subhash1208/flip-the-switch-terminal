import pytest

from bailiff.redact import MARKER, redact

PII_CASES = [
    # 1. email: SSH remotes and dotless domains are left alone
    ("alice@example.com", "[redacted:email]", 1),
    ("first.last+tag@sub.example.co.uk", "[redacted:email]", 1),
    ("mail bob_x@corp.io.", "mail [redacted:email].", 1),
    ("x@a.bc", "[redacted:email]", 1),
    ("contact: dev%ops@mail-srv.example.org ok", "contact: [redacted:email] ok", 1),
    ("git@github.com:owner/repo.git", "git@github.com:owner/repo.git", 0),
    ("user@localhost", "user@localhost", 0),
    ("@example.com", "@example.com", 0),
    ("a@b.c", "a@b.c", 0),
    # 2. home paths: the user name goes, the rest of the path stays
    (r"C:\Users\alice\AppData", r"C:\Users\[redacted:user]\AppData", 1),
    ("C:/Users/alice/x", "C:/Users/[redacted:user]/x", 1),
    (r"c:\users\alice", r"c:\users\[redacted:user]", 1),
    (r"C:\Users\John Smith\Desktop", r"C:\Users\[redacted:user]\Desktop", 1),
    ("/Users/alice/Desktop", "/Users/[redacted:user]/Desktop", 1),
    ("/home/bob/src", "/home/[redacted:user]/src", 1),
    ("/home/runner/work", "/home/[redacted:user]/work", 1),
    (r"C:\Users\Public\x", r"C:\Users\Public\x", 0),
    (r"C:\Users\Default\x", r"C:\Users\Default\x", 0),
    (r"C:\Users\All Users\x", r"C:\Users\All Users\x", 0),
    (r"C:\Users\Default User\x", r"C:\Users\Default User\x", 0),
    ("/Users/Shared/x", "/Users/Shared/x", 0),
    ("/root", "/root", 0),
    (r"Users\alice", r"Users\alice", 0),
    ("/Users/[redacted:user]", "/Users/[redacted:user]", 0),
    # 3. identity env lines
    ("USER=alice", "USER=[redacted:user]", 1),
    ("LOGNAME=bob", "LOGNAME=[redacted:user]", 1),
    ("USERNAME=John Smith", "USERNAME=[redacted:user]", 1),
    ("HOSTNAME=box.local", "HOSTNAME=[redacted:host]", 1),
    ("COMPUTERNAME=DESKTOP-7Q2", "COMPUTERNAME=[redacted:host]", 1),
    ("export HOST=box.local", "export HOST=[redacted:host]", 1),
    ("TZ=UTC USER=alice LANG=en", "TZ=UTC USER=[redacted:user] LANG=en", 1),
    ("GIT_USER=x", "GIT_USER=x", 0),
    ("USERX=y", "USERX=y", 0),
    ("LOCALHOST=1", "LOCALHOST=1", 0),
    ("HOME=/Users/alice&LANG=en", "HOME=/Users/[redacted:user]&LANG=en", 1),
    # 4. the hostname in uname -a; kernel, release and arch survive
    (
        "Linux bob-staging 6.8.0-45-generic #45-Ubuntu SMP x86_64 GNU/Linux",
        "Linux [redacted:host] 6.8.0-45-generic #45-Ubuntu SMP x86_64 GNU/Linux",
        1,
    ),
    (
        "Darwin alices-mac.local 24.1.0 Darwin Kernel Version 24.1.0 arm64",
        "Darwin [redacted:host] 24.1.0 Darwin Kernel Version 24.1.0 arm64",
        1,
    ),
    ("FreeBSD box 14.0-RELEASE amd64", "FreeBSD [redacted:host] 14.0-RELEASE amd64", 1),
    ("MINGW64_NT-10.0-19045 box 3.5.3", "MINGW64_NT-10.0-19045 [redacted:host] 3.5.3", 1),
    ("Linux is great", "Linux is great", 0),
    # 5. MAC address
    ("aa:bb:cc:dd:ee:ff", "[redacted:mac]", 1),
    ("AA-BB-CC-DD-EE-FF", "[redacted:mac]", 1),
    ("nic 00:1b:44:11:3a:b7 up", "nic [redacted:mac] up", 1),
    ("aa:bb:cc:dd:ee", "aa:bb:cc:dd:ee", 0),
    ("aa:bb:cc:dd:ee:ff:00", "aa:bb:cc:dd:ee:ff:00", 0),
    # 6. IPv6: valid addresses only; clock times and C++ scopes are not addresses
    ("2001:db8::1", "[redacted:ip]", 1),
    ("fe80::1ff:fe23:4567", "[redacted:ip]", 1),
    ("addr=2001:db8::5 up", "addr=[redacted:ip] up", 1),
    ("::ffff:1.2.3.4", "::ffff:[redacted:ip]", 1),
    ("::1", "::1", 0),
    ("12:30:45", "12:30:45", 0),
    ("2026-11-06T17:11:33", "2026-11-06T17:11:33", 0),
    ("std::vector", "std::vector", 0),
    ("ab::cd", "ab::cd", 0),
    # 7. IPv4: octet-validated; loopback and unspecified kept; versions kept
    ("10.0.0.1", "[redacted:ip]", 1),
    ("ip 192.168.1.20 port", "ip [redacted:ip] port", 1),
    ("8.8.8.8", "[redacted:ip]", 1),
    ("127.0.0.2", "[redacted:ip]", 1),
    ("127.0.0.1", "127.0.0.1", 0),
    ("0.0.0.0", "0.0.0.0", 0),
    ("v22.11.0", "v22.11.0", 0),
    ("v22.11.0.4", "v22.11.0.4", 0),
    ("6.8.0-45-generic", "6.8.0-45-generic", 0),
    ("10.0.19045.4894", "10.0.19045.4894", 0),
    ("256.1.1.1", "256.1.1.1", 0),
    ("01.2.3.4", "01.2.3.4", 0),
    ("1.2.3.4.5", "1.2.3.4.5", 0),
    ("1.2.3", "1.2.3", 0),
    # 8. card numbers: Luhn-valid only; UUIDs and timestamps are not cards
    ("4111 1111 1111 1111", "[redacted:card]", 1),
    ("4111-1111-1111-1111", "[redacted:card]", 1),
    ("4111111111111111", "[redacted:card]", 1),
    ("378282246310005", "[redacted:card]", 1),
    ("4111 1111 1111 1112", "4111 1111 1111 1112", 0),
    ("timestamp=4111111111111111", "timestamp=4111111111111111", 0),
    ("items: 4111111111111111", "items: [redacted:card]", 1),
    ("12345678-1234-1234-1234-123456789012", "12345678-1234-1234-1234-123456789012", 0),
    # 9. US SSN
    ("123-45-6789", "[redacted:ssn]", 1),
    ("ssn 123-45-6789.", "ssn [redacted:ssn].", 1),
    ("000-12-3456", "000-12-3456", 0),
    ("666-12-3456", "666-12-3456", 0),
    ("900-12-3456", "900-12-3456", 0),
    ("123-45-67890", "123-45-67890", 0),
    # 10. phone: E.164 only
    ("+14155550123", "[redacted:phone]", 1),
    ("call +442071838750 now", "call [redacted:phone] now", 1),
    ("+1 415 555 0123", "+1 415 555 0123", 0),
    ("a+14155550123", "a+14155550123", 0),
    ("+0123456789", "+0123456789", 0),
    # 11. long numeric IDs; epoch and nanosecond timestamps are not IDs
    ("123456789012345", "[redacted:id]", 1),
    ("id=123456789012345678", "id=[redacted:id]", 1),
    ("timestamp_ms=1700000000000", "timestamp_ms=1700000000000", 0),
    ("nanos=1700000000000000000", "nanos=1700000000000000000", 0),
    ("12345678901234567890", "12345678901234567890", 0),
    (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        0,
    ),
    ("2026-11-06T17:11:33+05:30", "2026-11-06T17:11:33+05:30", 0),
]


@pytest.mark.parametrize(("text", "expected", "hits"), PII_CASES)
def test_pii_rule_masks_or_leaves_text_alone(text: str, expected: str, hits: int) -> None:
    out, count = redact(text)
    assert out == expected
    assert count == hits
    assert redact(out) == (out, 0)


def test_each_masked_item_counts_as_one_hit() -> None:
    assert redact("alice@example.com and bob@example.org") == (
        "[redacted:email] and [redacted:email]",
        2,
    )


def test_a_secret_is_masked_before_the_pii_rules_see_it() -> None:
    assert redact("DATABASE_PASSWORD=bob@example.com") == (f"DATABASE_PASSWORD={MARKER}", 1)


def test_a_home_path_in_an_env_line_keeps_the_key_and_the_rest_of_the_path() -> None:
    assert redact("HOME=/Users/alice/.config/app") == (
        "HOME=/Users/[redacted:user]/.config/app",
        1,
    )


def test_line_rules_also_fire_inside_a_json_envelope_where_newlines_are_escaped() -> None:
    text = (
        r'{"stdout": "Darwin alices-mac.local 24.5.0 Darwin Kernel\nUSERNAME=John Smith\n'
        r'HOSTNAME=box\n", "exit_code": 0}'
    )
    out, hits = redact(text)
    assert out == (
        r'{"stdout": "Darwin [redacted:host] 24.5.0 Darwin Kernel\nUSERNAME=[redacted:user]\n'
        r'HOSTNAME=[redacted:host]\n", "exit_code": 0}'
    )
    assert hits == 3
    assert "alices-mac" not in out and "Smith" not in out
