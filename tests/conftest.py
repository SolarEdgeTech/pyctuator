import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generator, Optional, Dict

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
# pylint: disable=too-many-instance-attributes
class Endpoints:
    root: str
    pyctuator: str
    env: str
    info: str
    health: str
    metrics: str
    loggers: str
    threads: str
    logfile: str
    httptrace: str


@dataclass
class RegistrationTrackerFixture:
    registration: Optional[RegistrationRequest]
    count: int
    start_time: Optional[str]
    deregistration_time: Optional[datetime]
    test_start_time: datetime


class CustomServer(Server):
    def install_signal_handlers(self) -> None:
        pass


@pytest.fixture
def registration_tracker() -> RegistrationTrackerFixture:
    return RegistrationTrackerFixture(None, 0, None, None, datetime.now(timezone.utc))


@pytest.fixture
def boot_admin_server(registration_tracker: RegistrationTrackerFixture) -> Generator:
    boot_admin_app = FastAPI(
        title="Boot Admin Mock Server",
        description="Demonstrate Spring Boot Admin Integration with FastAPI",
        docs_url="/api",
    )

    # pylint: disable=unused-argument,unused-variable
    @boot_admin_app.post("/register", tags=["admin-server"])
    def register(request: Request, registration: RegistrationRequest) -> Dict[str, str]:
        logging.debug("Got registration post %s, %d registrations since %s",
                      registration, registration_tracker.count, registration_tracker.start_time)
        registration_tracker.registration = registration
        registration_tracker.count += 1
        if registration_tracker.start_time is None:
            registration_tracker.start_time = registration.metadata["startup"]
        return {"id": "JB007"}

    # pylint: disable=unused-argument,unused-variable
    @boot_admin_app.delete("/register/{registration_id}", tags=["admin-server"])
    def deregister(registration_id: str) -> None:
        logging.debug("Got deregistration, delete %s (previous deregistration time is %s)",
                      registration_id, registration_tracker.deregistration_time)
        registration_tracker.deregistration_time = datetime.now(timezone.utc)

    # Start the mock boot-admin server that is needed to test pyctuator's registration
    boot_admin_config = Config(app=boot_admin_app, port=8001, loop="asyncio")
    boot_admin_server = CustomServer(config=boot_admin_config)
    boot_admin_thread = threading.Thread(target=boot_admin_server.run)
    boot_admin_thread.start()
    while not boot_admin_server.started:
        time.sleep(0.01)

    # Yield back to pytest until the module is done
    yield None

    boot_admin_server.should_exit = True
    boot_admin_server.force_exit = True
    boot_admin_thread.join()


@pytest.mark.usefixtures("boot_admin_server")
@pytest.fixture
def endpoints(registration_tracker: RegistrationTrackerFixture) -> Endpoints:
    # time.sleep(600)
    # Wait for pyctuator to register with the boot-admin at least once
    while registration_tracker.registration is None:
        time.sleep(0.01)

    assert isinstance(registration_tracker.registration, RegistrationRequest)

    response = requests.get(registration_tracker.registration.managementUrl)
    assert response.status_code == 200

    links = response.json()["_links"]
    return Endpoints(
        root=registration_tracker.registration.serviceUrl,
        pyctuator=links["self"]["href"],
        env=links["env"]["href"],
        info=links["info"]["href"],
        health=links["health"]["href"],
        metrics=links["metrics"]["href"],
        loggers=links["loggers"]["href"],
        threads=links["threaddump"]["href"],
        logfile=links["logfile"]["href"],
        httptrace=links["httptrace"]["href"],
    )


class PyctuatorServer(ABC):

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def atexit(self) -> None:
        pass
