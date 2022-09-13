from abc import ABC
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus

from typing import Mapping


class Status(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


@dataclass
class HealthDetails:
    pass


@dataclass
class HealthStatus:
    status: Status
    details: HealthDetails


@dataclass
class HealthSummary:
    status: Status
    details: Mapping[str, HealthStatus]

    def http_status(self) -> int:
        if self.status == Status.DOWN:
            return HTTPStatus.SERVICE_UNAVAILABLE
        return HTTPStatus.OK


class HealthProvider(ABC):
    def is_supported(self) -> bool:
        pass

    def get_name(self) -> str:
        pass

    def get_health(self) -> HealthStatus:
        pass
