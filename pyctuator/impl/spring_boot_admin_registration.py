import http.client
import json
import logging
import os
import ssl
import threading
import urllib.parse
from base64 import b64encode
from datetime import datetime
from http.client import HTTPConnection, HTTPResponse
from typing import Optional, Dict

from pyctuator.auth import Auth, BasicAuth


# pylint: disable=too-many-instance-attributes
class BootAdminRegistrationHandler:

    def __init__(
            self,
            registration_url: str,
            registration_auth: Optional[Auth],
            application_name: str,
            pyctuator_base_url: str,
            start_time: datetime,
            service_url: str,
            registration_interval_sec: float,
            application_metadata: Optional[dict] = None
    ) -> None:
        self.registration_url = registration_url
        self.registration_auth = registration_auth
        self.application_name = application_name
        self.pyctuator_base_url = pyctuator_base_url
        self.start_time = start_time
        self.service_url = service_url if service_url.endswith("/") else service_url + "/"
        self.registration_interval_sec = registration_interval_sec
        self.instance_id = None
        self.application_metadata = application_metadata if application_metadata else {}

        self.should_continue_registration_schedule: bool = False
        self.disable_certificate_validation_for_https_registration: bool = \
            os.getenv("PYCTUATOR_REGISTRATION_NO_CERT") is not None

    def _schedule_next_registration(self, registration_interval_sec: float) -> None:
        timer = threading.Timer(
            registration_interval_sec,
            self._register_with_admin_server,
            []
        )
        timer.setDaemon(True)
        timer.start()

    def _register_with_admin_server(self) -> None:
        # When waking up, make sure registration is still needed
        if not self.should_continue_registration_schedule:
            return

        registration_data = {
            "name": self.application_name,
            "managementUrl": self.pyctuator_base_url,
            "healthUrl": f"{self.pyctuator_base_url}/health",
            "serviceUrl": self.service_url,
            "metadata": {
                "startup": self.start_time.isoformat(),
                **self.application_metadata
            }
        }

        logging.debug("Trying to post registration data to %s: %s", self.registration_url, registration_data)

        conn: Optional[HTTPConnection] = None
        try:
            headers = {"Content-type": "application/json"}
            self.authenticate(headers)

            response = self._http_request(self.registration_url, "POST", headers, json.dumps(registration_data))

            if response.status < 200 or response.status >= 300:
                logging.warning("Failed registering with boot-admin, got %s - %s", response.status, response.read())
            else:
                self.instance_id = json.loads(response.read().decode('utf-8'))["id"]

        except Exception as e:  # pylint: disable=broad-except
            logging.warning("Failed registering with boot-admin, %s (%s)", e, type(e))

        finally:
            if conn:
                conn.close()

        # Schedule the next registration unless asked to abort
        if self.should_continue_registration_schedule:
            self._schedule_next_registration(self.registration_interval_sec)

    def deregister_from_admin_server(self) -> None:
        if self.instance_id is None:
            return

        headers = {}
        self.authenticate(headers)

        deregistration_url = f"{self.registration_url}/{self.instance_id}"
        logging.info("Deregistering from %s", deregistration_url)

        conn: Optional[HTTPConnection] = None
        try:
            response = self._http_request(deregistration_url, "DELETE", headers)

            if response.status < 200 or response.status >= 300:
                logging.warning("Failed deregistering from boot-admin, got %s - %s", response.status, response.read())

        except Exception as e:  # pylint: disable=broad-except
            logging.warning("Failed deregistering from boot-admin, %s (%s)", e, type(e))

        finally:
            if conn:
                conn.close()

    def authenticate(self, headers: Dict) -> None:
        if isinstance(self.registration_auth, BasicAuth):
            password = self.registration_auth.password if self.registration_auth.password else ""
            authorization_string = self.registration_auth.username + ":" + password
            encoded_authorization: str = b64encode(bytes(authorization_string, "utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {encoded_authorization}"

    def start(self, initial_delay_sec: float = None) -> None:
        logging.info("Starting recurring registration of %s with %s",
                     self.pyctuator_base_url, self.registration_url)
        self.should_continue_registration_schedule = True
        self._schedule_next_registration(initial_delay_sec or self.registration_interval_sec)

    def stop(self) -> None:
        logging.info("Stopping recurring registration")
        self.should_continue_registration_schedule = False

    def _http_request(self, url: str, method: str, headers: Dict[str, str], body: Optional[str] = None) -> HTTPResponse:
        url_parts = urllib.parse.urlsplit(url)
        if url_parts.scheme == "http":
            conn = http.client.HTTPConnection(url_parts.hostname, url_parts.port)
        elif url_parts.scheme == "https":
            context = None
            if self.disable_certificate_validation_for_https_registration:
                context = ssl.SSLContext()
                context.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(url_parts.hostname, url_parts.port, context=context)
        else:
            raise ValueError(f"Unknown scheme in {url}")

        conn.request(
            method,
            url_parts.path,
            body=body,
            headers=headers,
        )
        return conn.getresponse()
