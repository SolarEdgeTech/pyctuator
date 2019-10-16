import logging
import threading
import time
from datetime import datetime

# TODO use stdlib instead of requests
import requests

# TODO get interval from config
registration_interval = 1

should_continue_registration_schedule: bool = True


def _schedule_next_registration(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str
) -> None:
    timer = threading.Timer(
        registration_interval,
        _register_with_admin_server,
        [
            registration_url,
            application_name,
            actuator_base_url,
            start_time,
            service_url
        ]
    )
    timer.setDaemon(True)
    timer.start()


def _register_with_admin_server(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str
) -> None:
    registration_data = {
        "name": application_name,
        "managementUrl": actuator_base_url,
        "healthUrl": f"{actuator_base_url}/health",
        "serviceUrl": service_url,
        "metadata": {"startup": start_time.isoformat()}
    }

    logging.debug("Trying to post registration data to %s: %s", registration_url, registration_data)

    try:
        response = requests.post(
            registration_url,
            json=registration_data)

        if response.status_code < 200 or response.status_code >= 300:
            logging.warning("Failed registering with boot-admin, got %s - %s", response.status_code, response.reason)

    except Exception as e:  # pylint: disable=broad-except
        logging.warning("Failed registering with boot-admin, caught %s", type(e))

    # Schedule the next registration unless asked to abort
    global should_continue_registration_schedule
    if should_continue_registration_schedule:
        _schedule_next_registration(
            registration_url,
            application_name,
            actuator_base_url,
            start_time,
            service_url
        )
    else:
        # Signal that the loop is stopped and we are ready for startup again
        should_continue_registration_schedule = True


def start_recurring_registration_with_admin_server(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str
) -> None:
    global should_continue_registration_schedule
    should_continue_registration_schedule = True

    _register_with_admin_server(
        registration_url,
        application_name,
        actuator_base_url,
        start_time,
        service_url
    )


def stop_recurring_registration() -> None:
    logging.debug("Stopping recurring registration")
    global should_continue_registration_schedule
    should_continue_registration_schedule = False
    while not should_continue_registration_schedule:
        time.sleep(0.1)
