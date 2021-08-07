import pytest

from pyctuator.health.health_provider import HealthStatus, Status, HealthDetails, HealthProvider
from pyctuator.impl.pyctuator_impl import PyctuatorImpl, AppInfo, AppDetails
from pyctuator.pyctuator import default_logfile_format


class MyHealthProvider(HealthProvider):
    def __init__(self, name: str = "kuki") -> None:
        self.name = name
        self.status = Status.UNKNOWN

    def down(self) -> None:
        self.status = Status.DOWN

    def up(self) -> None:
        self.status = Status.UP

    def is_supported(self) -> bool:
        return True

    def get_health(self) -> HealthStatus:
        return HealthStatus(self.status, HealthDetails())

    def get_name(self) -> str:
        return self.name


@pytest.fixture
def pyctuator_impl() -> PyctuatorImpl:
    return PyctuatorImpl(
        AppInfo(app=AppDetails(name="appy")),
        "http://appy/pyctuator",
        10,
        default_logfile_format,
        None,
    )


def test_health_status_single_provider(pyctuator_impl: PyctuatorImpl) -> None:
    health_provider = MyHealthProvider()
    pyctuator_impl.register_health_providers(health_provider)

    # Test's default status is UNKNOWN
    assert pyctuator_impl.get_health().status == Status.UNKNOWN

    health_provider.down()
    assert pyctuator_impl.get_health().status == Status.DOWN

    health_provider.up()
    assert pyctuator_impl.get_health().status == Status.UP


def test_health_status_multiple_providers(pyctuator_impl: PyctuatorImpl) -> None:
    health_providers = [MyHealthProvider("kuki"), MyHealthProvider("puki"), MyHealthProvider("ruki")]
    for health_provider in health_providers:
        pyctuator_impl.register_health_providers(health_provider)

    # Test's default status is UNKNOWN - all 3 are UNKNOWN
    assert pyctuator_impl.get_health().status == Status.UNKNOWN

    health_providers[0].down()
    assert pyctuator_impl.get_health().status == Status.DOWN

    health_providers[0].up()
    assert pyctuator_impl.get_health().status == Status.UP

    # first provider is UP, but the second is DOWN
    health_providers[1].down()
    assert pyctuator_impl.get_health().status == Status.DOWN

    # first and second providers are UP, 3rd is UNKNOWN
    health_providers[1].up()
    assert pyctuator_impl.get_health().status == Status.UP
