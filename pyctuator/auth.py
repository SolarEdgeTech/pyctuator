from dataclasses import dataclass
from typing import Optional


@dataclass
class Auth:
    pass


@dataclass
class BasicAuth(Auth):
    username: str
    password: Optional[str]
