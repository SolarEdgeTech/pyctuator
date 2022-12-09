import abc
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
        """
        :return: The HTTP according to the service's health. Done according to the documentation in
                 https://docs.spring.io/spring-boot/docs/2.7.0/reference/htmlsingle/#actuator.endpoints.health.writing-custom-health-indicators
                 The HTTP status code in the response reflects the overall health status. By default, OUT_OF_SERVICE
                 and DOWN map to 503. Any unmapped health statuses, including UP, map to 200.
        """
        if self.status == Status.DOWN:
            return HTTPStatus.SERVICE_UNAVAILABLE
        return HTTPStatus.OK


class HealthProvider(ABC):
    @abc.abstractmethod
    def is_supported(self) -> bool:
        pass

    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    def get_health(self) -> HealthStatus:
        pass
