import logging
import random
import secrets
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generator, Optional, Dict

import pytest
import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from starlette import status
from uvicorn.config import Config
from uvicorn.main import Server

from pyctuator.endpoints import Endpoints

REQUEST_TIMEOUT = 10


class RegistrationRequest(BaseModel):
    name: str
    managementUrl: str
    healthUrl: str
    serviceUrl: str
    metadata: dict


@dataclass
# pylint: disable=too-many-instance-attributes
class RegisteredEndpoints:
    root: str
    pyctuator: str
    env: Optional[str]
    info: Optional[str]
    health: Optional[str]
    metrics: Optional[str]
    loggers: Optional[str]
    threads: Optional[str]
    logfile: Optional[str]
    httptrace: Optional[str]


@dataclass
class RegistrationTrackerFixture:
    registration: Optional[RegistrationRequest]
    count: int
    start_time: Optional[str]
    deregistration_time: Optional[datetime]
    test_start_time: datetime


endpoint_href_path = {
    Endpoints.ENV: "env",
    Endpoints.INFO: "info",
    Endpoints.HEALTH: "health",
    Endpoints.METRICS: "metrics",
    Endpoints.LOGGERS: "loggers",
    Endpoints.THREAD_DUMP: "threaddump",
    Endpoints.LOGFILE: "logfile",
    Endpoints.HTTP_TRACE: "httptrace",
}


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

    security = HTTPBasic()

    def get_current_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
        correct_username = secrets.compare_digest(credentials.username, "moo")
        correct_password = secrets.compare_digest(credentials.password, "haha")
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Moo haha",
            )
        return credentials.username

    # pylint: disable=unused-variable
    @boot_admin_app.post("/register", tags=["admin-server"])
    def register(registration: RegistrationRequest) -> Dict[str, str]:
        logging.debug("Got registration post %s, %d registrations since %s",
                      registration, registration_tracker.count, registration_tracker.start_time)
        registration_tracker.registration = registration
        registration_tracker.count += 1
        if registration_tracker.start_time is None:
            registration_tracker.start_time = registration.metadata["startup"]
        return {"id": "JB007"}

    # pylint: disable=unused-variable
    @boot_admin_app.post("/register-with-basic-auth", tags=["admin-server"])
    def register_with_basic_auth(
            registration: RegistrationRequest,
            username: str = Depends(get_current_username)) -> Dict[str, str]:
        logging.debug("Got registration post %s from %s, %d registrations since %s",
                      registration, username, registration_tracker.count, registration_tracker.start_time)
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
    boot_admin_config = Config(app=boot_admin_app, port=8001, lifespan="off", log_level="info")
    boot_admin_server = CustomServer(config=boot_admin_config)
    boot_admin_thread = threading.Thread(target=boot_admin_server.run)
    boot_admin_thread.start()
    while not boot_admin_server.started:
        time.sleep(0.01)
    logging.info("Spring-boot-admin mock-server started")

    # Yield back to pytest until the module is done
    yield None

    logging.info("Stopping spring-boot-admin mock-server")
    boot_admin_server.should_exit = True
    boot_admin_server.force_exit = True
    boot_admin_thread.join()


@pytest.mark.usefixtures("boot_admin_server")
@pytest.fixture
def registered_endpoints(registration_tracker: RegistrationTrackerFixture) -> RegisteredEndpoints:
    # time.sleep(600)
    # Wait for pyctuator to register with the boot-admin at least once
    while registration_tracker.registration is None:
        time.sleep(0.01)

    assert isinstance(registration_tracker.registration, RegistrationRequest)

    response = requests.get(registration_tracker.registration.managementUrl, timeout=REQUEST_TIMEOUT)
    assert response.status_code == 200

    links = response.json()["_links"]

    def link_href(endpoint: Endpoints) -> Optional[str]:
        link = endpoint_href_path.get(endpoint)
        return str(links[link]["href"]) if link in links else None

    return RegisteredEndpoints(
        root=registration_tracker.registration.serviceUrl,
        pyctuator=links["self"]["href"],
        env=link_href(Endpoints.ENV),
        info=link_href(Endpoints.INFO),
        health=link_href(Endpoints.HEALTH),
        metrics=link_href(Endpoints.METRICS),
        loggers=link_href(Endpoints.LOGGERS),
        threads=link_href(Endpoints.THREAD_DUMP),
        logfile=link_href(Endpoints.LOGFILE),
        httptrace=link_href(Endpoints.HTTP_TRACE),
    )


class PyctuatorServer(ABC):
    metadata: Optional[dict] = {f"k{i}": f"v{i}" for i in range(random.randrange(10))}
    additional_app_info = {
        "serviceLinks": {
            "metrics": "http://xyz/service/metrics",
        },
        "podLinks": {
            "metrics": ["http://xyz/pod/metrics/memory", "http://xyz/pod/metrics/cpu"],
        },
    }

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def atexit(self) -> None:
        pass
