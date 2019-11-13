import http.client
import json
import logging
import threading
import time
import urllib.parse
from datetime import datetime

# TODO get interval from config
from http.client import HTTPConnection
from typing import Optional

should_continue_registration_schedule: bool = True


def _schedule_next_registration(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str,
        registration_interval_sec: int
) -> None:
    timer = threading.Timer(
        registration_interval_sec,
        _register_with_admin_server,
        [
            registration_url,
            application_name,
            actuator_base_url,
            start_time,
            service_url,
            registration_interval_sec,
        ]
    )
    timer.setDaemon(True)
    timer.start()


def _register_with_admin_server(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str,
        registration_interval_sec: int
) -> None:
    registration_data = {
        "name": application_name,
        "managementUrl": actuator_base_url,
        "healthUrl": f"{actuator_base_url}/health",
        "serviceUrl": service_url,
        "metadata": {"startup": start_time.isoformat()}
    }

    logging.debug("Trying to post registration data to %s: %s", registration_url, registration_data)

    conn: Optional[HTTPConnection] = None
    try:
        reg_url_split = urllib.parse.urlsplit(registration_url)
        conn = http.client.HTTPConnection(reg_url_split.hostname, reg_url_split.port)
        conn.request(
            "POST",
            reg_url_split.path,
            body=json.dumps(registration_data),
            headers={"Content-type": "application/json"})
        response = conn.getresponse()

        if response.status < 200 or response.status >= 300:
            logging.warning("Failed registering with boot-admin, got %s - %s", response.status, response.read())

    except Exception as e:  # pylint: disable=broad-except
        logging.warning("Failed registering with boot-admin, %s (%s)", e, type(e))

    finally:
        if conn:
            conn.close()

    # Schedule the next registration unless asked to abort
    global should_continue_registration_schedule
    if should_continue_registration_schedule:
        _schedule_next_registration(
            registration_url,
            application_name,
            actuator_base_url,
            start_time,
            service_url,
            registration_interval_sec
        )
    else:
        # Signal that the loop is stopped and we are ready for startup again
        should_continue_registration_schedule = True


def start_recurring_registration_with_admin_server(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str,
        registration_interval_sec: int,
) -> None:
    global should_continue_registration_schedule
    should_continue_registration_schedule = True

    _register_with_admin_server(
        registration_url,
        application_name,
        actuator_base_url,
        start_time,
        service_url,
        registration_interval_sec
    )


def stop_recurring_registration() -> None:
    logging.debug("Stopping recurring registration")
    global should_continue_registration_schedule
    should_continue_registration_schedule = False
    while not should_continue_registration_schedule:
        time.sleep(0.1)
