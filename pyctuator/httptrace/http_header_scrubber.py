import re

_keys_to_scrub = re.compile(
    "^(.*[^A-Za-z])?key([^A-Za-z].*)?$|"
    ".*secret.*|"
    ".*password.*|"
    ".*token.*|"
    ".*authorization.*|"
    ".*authentication.*|"
    ".*cookie.*",
    re.IGNORECASE
)


def scrub_header_value(key: str, value: str) -> str:
    if _keys_to_scrub.match(key):
        return "******"

    return value
