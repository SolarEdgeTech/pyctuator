from typing import Dict

from pyctuator.environment.custom_environment_provider import CustomEnvironmentProvider
from pyctuator.environment.environment_provider import PropertyValue
from pyctuator.environment.scrubber import SecretScrubber


def test_custom_environment_provider() -> None:
    def produce_env() -> Dict:
        return {
            "a": "s1",
            "b": {
                "secret": "ha ha",
                "c": 625,
            },
            "d": {
                "e": True,
                "f": "hello",
                "g": {
                    "h": 123,
                    "i": "abcde"
                }
            }
        }

    provider = CustomEnvironmentProvider("custom", produce_env)
    properties_source = provider.get_properties_source(SecretScrubber().scrub_secrets)
    assert properties_source.name == "custom"
    assert properties_source.properties == {
        "a": PropertyValue(value="s1"),
        "b.secret": PropertyValue(value="******"),
        "b.c": PropertyValue(value=625),
        "d.e": PropertyValue(value=True),
        "d.f": PropertyValue(value="hello"),
        "d.g.h": PropertyValue(value=123),
        "d.g.i": PropertyValue(value="abcde"),
    }
