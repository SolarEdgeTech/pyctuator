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


app = FastAPI(
    title="FastAPI example server",
    description="Demonstrate Spring Boot Admin Integration with FastAPI",
    docs_url="/api",
)
app.include_router(fastapi_actuator_endpoint.router)

registration_fixture = RegistrationFixture(None, 0, None,  datetime.now(timezone.utc))


@app.post("/register", tags=["admin-server"])
def register(request: Request, registration: RegistrationRequest) -> None:  # pylint: disable=unused-argument
    registration_fixture.registration = registration
    registration_fixture.count += 1
    if registration_fixture.start_time is None:
        registration_fixture.start_time = registration.metadata["startup"]


@pytest.fixture(scope="module")
def server() -> Generator:
    # Start a FastApi server that is integrated with actuator
    config = Config(app=app, loop="asyncio")
    server = CustomServer(config=config)
    thread = threading.Thread(target=server.run)
    thread.start()
    while not server.started or registration_fixture.registration is None:
        time.sleep(0.01)

    # Yield back to pytest until the module is done
    yield None

    # Once the module is done, stop the server and wait for the server's thread to finish
    fastapi_actuator_endpoint.should_exit = True
    server.should_exit = True
    thread.join()


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


@pytest.mark.usefixtures("server")
def test_self_endpoint(endpoints: Endpoints) -> None:
    response = requests.get(endpoints.actuator)
    assert response.status_code == 200
    assert response.json()["_links"] is not None


@pytest.mark.usefixtures("server")
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
    assert registration_start_time > registration_fixture.test_start_time - timedelta(seconds = 10)
