import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Generator, Optional

import pytest
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.requests import Request
from uvicorn.config import Config
from uvicorn.main import Server

from pyctuator import fastapi_actuator_endpoint


class RegistrationRequest(BaseModel):
    name: str
    managementUrl: str
    healthUrl: str
    serviceUrl: str
    metadata: dict


@dataclass
class Endpoints:
    actuator: str
    env: str
    info: str
    health: str


@dataclass
class RegistrationFixture:
    registration: Optional[RegistrationRequest]
    count: int
    start_time: Optional[str]
    test_start_time: datetime


class CustomServer(Server):
    def install_signal_handlers(self) -> None:
        pass


actuator_app = FastAPI(
    title="FastAPI Sxample Server",
    description="Demonstrate Spring Boot Admin Integration with FastAPI",
    docs_url="/api",
)
actuator_app.include_router(fastapi_actuator_endpoint.router)

boot_admin_app = FastAPI(
    title="Boot Admin Mock Server",
    description="Demonstrate Spring Boot Admin Integration with FastAPI",
    docs_url="/api",
)

registration_fixture = RegistrationFixture(None, 0, None, datetime.now(timezone.utc))


@boot_admin_app.post("/register", tags=["admin-server"])
def register(request: Request, registration: RegistrationRequest) -> None:  # pylint: disable=unused-argument
    registration_fixture.registration = registration
    registration_fixture.count += 1
    if registration_fixture.start_time is None:
        registration_fixture.start_time = registration.metadata["startup"]


@pytest.fixture(scope="module")
def boot_admin_server() -> Generator:
    # Start the mock boot-admin server that is needed to test teh actuator's registration
    boot_admin_config = Config(app=boot_admin_app, port=8001, loop="asyncio")
    boot_admin_server = CustomServer(config=boot_admin_config)
    boot_admin_thread = threading.Thread(target=boot_admin_server.run)
    boot_admin_thread.start()
    while not boot_admin_server.started:
        time.sleep(0.01)

    # Yield back to pytest until the module is done
    yield None

    boot_admin_server.should_exit = True
    boot_admin_thread.join()


@pytest.fixture(scope="module")
def actuator_server() -> Generator:
    # Start a the web-server in which the actuator is integrated
    actuator_config = Config(app=actuator_app, loop="asyncio")
    actuator_server = CustomServer(config=actuator_config)
    actuator_thread = threading.Thread(target=actuator_server.run)
    actuator_thread.start()
    while not actuator_server.started:
        time.sleep(0.01)

    # Wait for the actuator to register with the boot-admin at least once
    while registration_fixture.registration is None:
        time.sleep(0.01)

    # Yield back to pytest until the module is done
    yield None

    # Once the module is done, stop both servers and wait for their thread to finish
    fastapi_actuator_endpoint.should_exit = True
    actuator_server.should_exit = True
    actuator_thread.join()


@pytest.fixture
def endpoints() -> Endpoints:
    assert isinstance(registration_fixture.registration, RegistrationRequest)

    response = requests.get(registration_fixture.registration.managementUrl)
    assert response.status_code == 200

    links = response.json()["_links"]
    return Endpoints(
        actuator=links["self"]["href"],
        env=links["env"]["href"],
        info=links["info"]["href"],
        health=links["health"]["href"],
    )


@pytest.mark.usefixtures("boot_admin_server", "actuator_server")
def test_self_endpoint(endpoints: Endpoints) -> None:
    response = requests.get(endpoints.actuator)
    assert response.status_code == 200
    assert response.json()["_links"] is not None


@pytest.mark.usefixtures("boot_admin_server", "actuator_server")
def test_recurring_registration() -> None:
    # Verify that at least 3 registrations occured within 6 seconds since the test started
    start = time.time()
    while registration_fixture.count < 3:
        time.sleep(0.5)
        if time.time() - start > 6:
            pytest.fail(
                f"Expected at least 3 recurring registrations within 6 seconds but got {registration_fixture.count}")

    # Verify that the reported startup time is the same across all the registrations and that its later then the test's
    # start time
    assert registration_fixture.start_time == registration_fixture.registration.metadata["startup"]
    registration_start_time = datetime.fromisoformat(registration_fixture.start_time)
    assert registration_start_time > registration_fixture.test_start_time - timedelta(seconds=10)
