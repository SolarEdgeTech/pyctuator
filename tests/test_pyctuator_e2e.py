import time
from datetime import datetime, timedelta
from typing import Generator

import pytest
import requests

from tests.conftest import Endpoints, registration_fixture, ActuatorServer, RegistrationRequest
from tests.fast_api_test_server import FastApiActuatorServer


@pytest.fixture(scope="module", params=[FastApiActuatorServer], ids=["FastAPI"])
def actuator_server(request) -> Generator:  # type: ignore
    # Start a the web-server in which the actuator is integrated
    actuator_server: ActuatorServer = request.param()
    actuator_server.start()

    # Yield back to pytest until the module is done
    yield None

    # Once the module is done, stop the actuator-server
    actuator_server.stop()


@pytest.mark.usefixtures("boot_admin_server", "actuator_server")
def test_self_endpoint(endpoints: Endpoints) -> None:
    response = requests.get(endpoints.actuator)
    assert response.status_code == 200
    assert response.json()["_links"] is not None


@pytest.mark.usefixtures("boot_admin_server", "actuator_server")
def test_recurring_registration() -> None:
    # Verify that at least 3 registrations occurred within 6 seconds since the test started
    start = time.time()
    while registration_fixture.count < 3:
        time.sleep(0.5)
        if time.time() - start > 6:
            pytest.fail(
                f"Expected at least 3 recurring registrations within 6 seconds but got {registration_fixture.count}")

    # Verify that the reported startup time is the same across all the registrations and that its later then the test's
    # start time
    assert isinstance(registration_fixture.registration, RegistrationRequest)
    assert registration_fixture.start_time == registration_fixture.registration.metadata["startup"]
    registration_start_time = datetime.fromisoformat(registration_fixture.start_time)
    assert registration_start_time > registration_fixture.test_start_time - timedelta(seconds=10)
