import time
from datetime import datetime
from typing import Optional, Any

import pytest

from pyctuator.auth import Auth, BasicAuth
from pyctuator.impl.spring_boot_admin_registration import BootAdminRegistrationHandler
from tests.conftest import RegistrationTrackerFixture


@pytest.mark.usefixtures("boot_admin_server")
def test_registration_no_auth(registration_tracker: RegistrationTrackerFixture) -> None:
    registration_handler = get_registration_handler("http://localhost:8001/register", None)

    try:
        _start_registration(registration_handler)
        assert registration_tracker.count == 1

    finally:
        registration_handler.stop()


@pytest.mark.usefixtures("boot_admin_server")
def test_registration_basic_auth_no_creds(registration_tracker: RegistrationTrackerFixture, caplog: Any) -> None:
    registration_handler = get_registration_handler("http://localhost:8001/register-with-basic-auth", None)

    try:
        _start_registration(registration_handler)
        assert registration_tracker.count == 0

        error_message = "Failed registering with boot-admin, got %s - %s"
        assert error_message in [record.msg for record in caplog.records]

        error_args = (401, b'{"detail":"Not authenticated"}')
        assert error_args in [record.args for record in caplog.records if record.msg == error_message]

    finally:
        registration_handler.stop()


@pytest.mark.usefixtures("boot_admin_server")
def test_registration_basic_auth_bad_creds(registration_tracker: RegistrationTrackerFixture, caplog: Any) -> None:
    registration_handler = get_registration_handler(
        "http://localhost:8001/register-with-basic-auth",
        BasicAuth("kuki", "puki")
    )

    try:
        _start_registration(registration_handler)
        assert registration_tracker.count == 0

        error_message = "Failed registering with boot-admin, got %s - %s"
        assert error_message in [record.msg for record in caplog.records]

        error_args = (401, b'{"detail":"Moo haha"}')
        assert error_args in [record.args for record in caplog.records if record.msg == error_message]

    finally:
        registration_handler.stop()


@pytest.mark.usefixtures("boot_admin_server")
def test_registration_basic_auth(registration_tracker: RegistrationTrackerFixture) -> None:
    registration_handler = get_registration_handler(
        "http://localhost:8001/register-with-basic-auth",
        BasicAuth("moo", "haha")
    )

    try:
        _start_registration(registration_handler)
        assert registration_tracker.count == 1

    finally:
        registration_handler.stop()


def get_registration_handler(registration_url: str, registration_auth: Optional[Auth]) -> BootAdminRegistrationHandler:
    return BootAdminRegistrationHandler(
        registration_url=registration_url,
        registration_auth=registration_auth,
        application_name="noauth",
        pyctuator_base_url="http://whatever/pyctuator",
        start_time=datetime.now(),
        service_url="http://whatever/service",
        registration_interval_sec=100
    )


def _start_registration(registration_handler: BootAdminRegistrationHandler) -> None:
    # Registration is done asynchronously, for the test, ask to register shortly after start is called
    registration_handler.start(0.01)

    # Wait enough after starting the registration allowing the async registration to happen.
    time.sleep(0.1)
