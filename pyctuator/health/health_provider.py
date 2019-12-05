from abc import ABC
from dataclasses import dataclass

from typing import Mapping


@dataclass
class HealthDetails:
    pass


@dataclass
class HealthStatus:
    status: str
    details: HealthDetails


@dataclass
class HealthSummary:
    status: str
    details: Mapping[str, HealthStatus]


class HealthProvider(ABC):
    def is_supported(self) -> bool:
        pass

    def get_name(self) -> str:
        pass

    def get_health(self) -> HealthStatus:
        pass
