from pyctuator.environment.scrubber import scrub_secrets


def test_scrub_secrets() -> None:
    with_secrets = {
        "some.value": "Good",
        "another.value": 10,
        "another.value.and.another": 10.0,
        "a.boolean": True,
        "some.api_key": "Bad",
        "a.key": "Bad",
        "a.keyboard": "Good",
        "db.url.1": "mysql+pymysql://user:Bad@host:3306/schema",
        "db.url.2": "mysql+pymysql://joe:Bad@host/schema",
        "db.url.3": "mysql+pymysql://joe:Bad@host",
        "db.url.4": "mysql+pymysql://host",
    }

    expected_without_secrets = {
        "some.value": "Good",
        "another.value": 10,
        "another.value.and.another": 10.0,
        "a.boolean": True,
        "some.api_key": "******",
        "a.key": "******",
        "a.keyboard": "Good",
        "db.url.1": "mysql+pymysql://user:******@host:3306/schema",
        "db.url.2": "mysql+pymysql://joe:******@host/schema",
        "db.url.3": "mysql+pymysql://joe:******@host",
        "db.url.4": "mysql+pymysql://host",
    }

    scrubbed = scrub_secrets(with_secrets)
    assert scrubbed == expected_without_secrets
