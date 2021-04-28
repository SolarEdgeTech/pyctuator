import pytest
from pyctuator.httptrace.http_header_scrubber import scrub_header_value


@pytest.mark.parametrize("key,value", [
    ("Authorization", "Bearer 123"),
    ("authorization", "Bearer 123"),
    ("X-Csrf-Token", "foo"),
    ("authentication", "secret123"),
    ("COOKIE", "my-logged-in-session")
])
def test_scrubbing(key: str, value: str) -> None:
    assert scrub_header_value(key, value) == "******"


@pytest.mark.parametrize("key,value", [("Host", "example.org"), ("Content-Length", "2000")])
def test_non_scrubbing(key: str, value: str) -> None:
    assert scrub_header_value(key, value) == value
