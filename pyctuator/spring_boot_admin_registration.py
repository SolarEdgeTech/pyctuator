import logging
import threading
from datetime import datetime

# TODO use stdlib instead of requests
import requests

# TODO get interval from config
registration_interval = 1


def schedule_next_registration(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str
) -> None:
    timer = threading.Timer(
        registration_interval,
        register_with_admin_server,
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


def register_with_admin_server(
        registration_url: str,
        application_name: str,
        actuator_base_url: str,
        start_time: datetime,
        service_url: str
) -> None:
    try:
        response = requests.post(
            registration_url,
            json={
                "name": application_name,
                "managementUrl": actuator_base_url,
                "healthUrl": f"{actuator_base_url}/health",
                "serviceUrl": service_url,
                "metadata": {"startup": start_time.isoformat()}
            })

        if response.status_code < 200 or response.status_code >= 300:
            logging.warning("Failed registering with boot-admin, got %s - %s", response.status_code, response.reason)

    except Exception as e:  # pylint: disable=broad-except
        logging.warning("Failed registering with boot-admin, caught %s", type(e))

    # Schedule the next registration
    schedule_next_registration(
        registration_url,
        application_name,
        actuator_base_url,
        start_time,
        service_url
    )
