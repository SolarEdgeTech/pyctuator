import logging
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
    metrics: str


@dataclass
class RegistrationTrackerFixture:
    registration: Optional[RegistrationRequest]
    count: int
    start_time: Optional[str]
    test_start_time: datetime


class CustomServer(Server):
    def install_signal_handlers(self) -> None:
        pass


@pytest.fixture
def registration_tracker() -> RegistrationTrackerFixture:
    return RegistrationTrackerFixture(None, 0, None, datetime.now(timezone.utc))


@pytest.fixture
def boot_admin_server(registration_tracker: RegistrationTrackerFixture) -> Generator:
    boot_admin_app = FastAPI(
        title="Boot Admin Mock Server",
        description="Demonstrate Spring Boot Admin Integration with FastAPI",
        docs_url="/api",
    )

    # pylint: disable=unused-argument,unused-variable
    @boot_admin_app.post("/register", tags=["admin-server"])
    def register(request: Request, registration: RegistrationRequest) -> None:
        logging.debug("Got registration post %s - %s", registration, registration_tracker)
        registration_tracker.registration = registration
        registration_tracker.count += 1
        if registration_tracker.start_time is None:
            registration_tracker.start_time = registration.metadata["startup"]

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
def endpoints(registration_tracker: RegistrationTrackerFixture) -> Endpoints:
    # Wait for the actuator to register with the boot-admin at least once
    while registration_tracker.registration is None:
        time.sleep(0.01)

    assert isinstance(registration_tracker.registration, RegistrationRequest)

    response = requests.get(registration_tracker.registration.managementUrl)
    assert response.status_code == 200

    links = response.json()["_links"]
    return Endpoints(
        actuator=links["self"]["href"],
        env=links["env"]["href"],
        info=links["info"]["href"],
        health=links["health"]["href"],
        metrics=links["metrics"]["href"],
    )


class ActuatorServer(ABC):

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
