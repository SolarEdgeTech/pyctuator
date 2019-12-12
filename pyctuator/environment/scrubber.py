import re
from typing import Any, Dict

_keys_to_scrub = re.compile("^(.*[^A-Za-z])?key([^A-Za-z].*)?$|.*secret.*|.*password.*|.*token.*", re.IGNORECASE)
_url_keys_to_scrub = re.compile(".*url.*", re.IGNORECASE)


def scrub_secrets(mapping: Dict) -> Dict:
    """Scrubs secrets from a dictionary replacing them with stars

    :param mapping: a mapping with "primitive" values that may include secrets
    :return: a copy of the input mapping having all secrets replaced with stars
    """

    def scrub(key: Any, value: Any) -> Any:
        if _keys_to_scrub.match(key):
            return "******"

        if _url_keys_to_scrub.match(key):
            return re.sub(r"(.*//[^:]*:).*(@.*)", r"\1******\2", str(value))

        return value

    return {k: scrub(k, v) for (k, v) in mapping.items()}
