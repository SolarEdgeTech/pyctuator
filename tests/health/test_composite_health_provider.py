from dataclasses import dataclass

from pyctuator.health.composite_health_provider import CompositeHealthProvider, CompositeHealthStatus
from pyctuator.health.health_provider import HealthProvider, HealthStatus, Status, HealthDetails


@dataclass
class CustomHealthDetails(HealthDetails):
    details: str


class CustomHealthProvider(HealthProvider):

    def __init__(self, name: str, status: HealthStatus) -> None:
        super().__init__()
        self.name = name
        self.status = status

    def is_supported(self) -> bool:
        return True

    def get_name(self) -> str:
        return self.name

    def get_health(self) -> HealthStatus:
        return self.status


def test_composite_health_provider_no_providers() -> None:
    health_provider = CompositeHealthProvider(
        "comp1",
    )

    assert health_provider.get_name() == "comp1"

    assert health_provider.get_health() == CompositeHealthStatus(
        status=Status.UP,
        details={}
    )


def test_composite_health_provider_all_up() -> None:
    health_provider = CompositeHealthProvider(
        "comp2",
        CustomHealthProvider("hp1", HealthStatus(Status.UP, CustomHealthDetails("d1"))),
        CustomHealthProvider("hp2", HealthStatus(Status.UP, CustomHealthDetails("d2"))),
    )

    assert health_provider.get_name() == "comp2"

    assert health_provider.get_health() == CompositeHealthStatus(
        status=Status.UP,
        details={
            "hp1": HealthStatus(Status.UP, CustomHealthDetails("d1")),
            "hp2": HealthStatus(Status.UP, CustomHealthDetails("d2")),
        }
    )


def test_composite_health_provider_one_down() -> None:
    health_provider = CompositeHealthProvider(
        "comp3",
        CustomHealthProvider("hp1", HealthStatus(Status.UP, CustomHealthDetails("d1"))),
        CustomHealthProvider("hp2", HealthStatus(Status.DOWN, CustomHealthDetails("d2"))),
    )

    assert health_provider.get_name() == "comp3"

    assert health_provider.get_health() == CompositeHealthStatus(
        status=Status.DOWN,
        details={
            "hp1": HealthStatus(Status.UP, CustomHealthDetails("d1")),
            "hp2": HealthStatus(Status.DOWN, CustomHealthDetails("d2")),
        }
    )
