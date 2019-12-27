import importlib.util
import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from pyctuator.health.health_provider import HealthProvider, HealthStatus, Status, HealthDetails


@dataclass
class DbHealthDetails(HealthDetails):
    engine: str
    failure: Optional[str] = None


@dataclass
class DbHealthStatus(HealthStatus):
    status: Status
    details: DbHealthDetails


class DbHealthProvider(HealthProvider):

    def __init__(self, engine: Engine) -> None:
        super().__init__()
        self.engine = engine

    def is_supported(self) -> bool:
        return importlib.util.find_spec("sqlalchemy") is not None

    def get_name(self) -> str:
        return "db"

    def get_health(self) -> DbHealthStatus:
        expected = int(time.time() * 1000)
        try:
            res = self.engine.execute(f"SELECT {expected}")
            actual = next(res)[0]
            if expected == actual:
                return DbHealthStatus(status=Status.UP, details=DbHealthDetails(self.engine.name))

            return DbHealthStatus(
                status=Status.UNKNOWN,
                details=DbHealthDetails(self.engine.name, f"Selected {expected}, got {actual}"))

        except OperationalError as e:
            return DbHealthStatus(status=Status.DOWN, details=DbHealthDetails(self.engine.name, str(e)))
