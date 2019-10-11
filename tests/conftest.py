import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generator, Optional

import pytest
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.requests import Request
from uvicorn.config import Config
from uvicorn.main import Server


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


@pytest.mark.usefixtures("boot_admin_server")
@pytest.fixture
def endpoints() -> Endpoints:
    # Wait for the actuator to register with the boot-admin at least once
    while registration_fixture.registration is None:
        time.sleep(0.01)

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


class ActuatorServer(ABC):

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
