from dataclasses import dataclass
from typing import Mapping

from pyctuator.health.health_provider import HealthProvider, HealthStatus, Status


@dataclass
class CompositeHealthStatus(HealthStatus):
    status: Status
    details: Mapping[str, HealthStatus]  # type: ignore[assignment]


class CompositeHealthProvider(HealthProvider):

    def __init__(self, name: str, *health_providers: HealthProvider) -> None:
        super().__init__()
        self.name = name
        self.health_providers = health_providers

    def is_supported(self) -> bool:
        return True

    def get_name(self) -> str:
        return self.name

    def get_health(self) -> CompositeHealthStatus:
        health_statuses: Mapping[str, HealthStatus] = {
            provider.get_name(): provider.get_health()
            for provider in self.health_providers
            if provider.is_supported()
        }

        # Health is UP if no provider is registered
        if not health_statuses:
            return CompositeHealthStatus(Status.UP, health_statuses)

        # If there's at least one provider and any of the providers is DOWN, the service is DOWN
        service_is_down = any(health_status.status == Status.DOWN for health_status in health_statuses.values())
        if service_is_down:
            return CompositeHealthStatus(Status.DOWN, health_statuses)

        # If there's at least one provider and none of the providers is DOWN and at least one is UP, the service is UP
        service_is_up = any(health_status.status == Status.UP for health_status in health_statuses.values())
        if service_is_up:
            return CompositeHealthStatus(Status.UP, health_statuses)

        # else, all providers are unknown so the service is UNKNOWN
        return CompositeHealthStatus(Status.UNKNOWN, health_statuses)
