import importlib.util
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.engine import Engine

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

    def __init__(self, engine: Engine, name: str = "db") -> None:
        super().__init__()
        self.engine = engine
        self.name = name

    def is_supported(self) -> bool:
        return importlib.util.find_spec("sqlalchemy") is not None

    def get_name(self) -> str:
        return self.name

    def get_health(self) -> DbHealthStatus:
        try:
            with self.engine.connect() as conn:
                if self.engine.dialect.do_ping(conn.connection): # type: ignore[arg-type]
                    return DbHealthStatus(
                        status=Status.UP,
                        details=DbHealthDetails(self.engine.name)
                    )

            return DbHealthStatus(
                status=Status.UNKNOWN,
                details=DbHealthDetails(self.engine.name, "Pinging failed"))

        except Exception as e:  # pylint: disable=broad-except
            return DbHealthStatus(status=Status.DOWN, details=DbHealthDetails(self.engine.name, str(e)))
