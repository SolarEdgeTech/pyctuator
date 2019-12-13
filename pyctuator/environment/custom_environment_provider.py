from typing import Callable, Dict

from pyctuator.environment.environment_provider import PropertiesSource, EnvironmentProvider, PropertyValue
from pyctuator.environment.scrubber import scrub_secrets


def _flatten(prefix: str, dict_to_flatten: Dict) -> Dict:
    """
    Recursively flattens a dictionary that may contain literal values (numbers and strings) and other dictionaries.
    For example, given the following dictionary: {
        "a": 1,
        "b": {
            "c": 2
            "d": {
                "e": 3
            }
        }
    }
    The flattened dictionary will be: {
        "a": 1,
        "b.c": 2,
        "b.d.e": 3
    }

    :param prefix: when descending to a sub-dictionary, the prefix represents the keys higher in the hierarchy
    :param dict_to_flatten: a dictionary, or a sub-dictionary to be flattened
    :return: a dictionary from a dot-separated key to a literal value
    """
    res: Dict = {}
    for key, value in dict_to_flatten.items():
        key_with_prefix = f"{prefix}{key}."
        if isinstance(value, dict):
            res = {**res, **_flatten(key_with_prefix, value)}
        else:
            res[key_with_prefix[:-1]] = value
    return res


class CustomEnvironmentProvider(EnvironmentProvider):

    def __init__(self, name: str, env_provider: Callable[[], Dict]) -> None:
        self.name = name
        self.env_provider = env_provider

    def get_properties_source(self) -> PropertiesSource:
        flattened_env = _flatten("", self.env_provider())
        scrubbed_env = scrub_secrets(flattened_env)
        properties_dict = {key: PropertyValue(value) for (key, value) in scrubbed_env.items()}
        return PropertiesSource(self.name, properties_dict)
