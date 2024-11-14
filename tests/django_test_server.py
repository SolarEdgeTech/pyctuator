import logging

import threading

from pyctuator.endpoints import Endpoints
from pyctuator.pyctuator import Pyctuator

import time
import requests
from wsgiref.simple_server import make_server

from tests.conftest import PyctuatorServer

from django.http.response import HttpResponse
from django.conf import settings
from django.core.servers.basehttp import (
    get_wsgi_application,
)

from django.urls import path

bind_port = 10000
REQUEST_TIMEOUT = 10

settings.configure(
    LOGGING_CONFIG=None,
    ROOT_URLCONF="tests.django_test_server",
    MIDDLEWARE=[
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
    ],
    DEBUG=False,
    ALLOWED_HOSTS=["127.0.0.1", "localhost"],
    SECRET_KEY="pyctuator-key",
)


def index_view(request):
    return HttpResponse()


def httptrace_test_url_view(request):
    sleep_sec = request.GET.get("sleep_sec", None)
    if sleep_sec:
        logging.info(f"Sleeping {sleep_sec} seconds before replying")
        time.sleep(int(sleep_sec))

    response = HttpResponse(b"my content")
    response["resp-data"] = request.headers.get("user-data")
    response["response-secret"] = "my password"

    return response


def logfile_test_repeater_view(request):
    repeated_string = request.GET.get("repeated_string", None)
    logging.error(repeated_string)

    return HttpResponse(repeated_string)


urlpatterns = [
    path("", index_view),
    path("httptrace_test_url", httptrace_test_url_view),
    path("logfile_test_repeater", logfile_test_repeater_view),
]


class DjangoPyctuatorServer(PyctuatorServer):
    def __init__(self, disabled_endpoints: Endpoints = Endpoints.NONE) -> None:
        global bind_port
        self.port = bind_port
        bind_port += 1

        self.app = get_wsgi_application()
        self.server = make_server("127.0.0.1", self.port, self.app)
        self.thread = threading.Thread(target=self.server.serve_forever)

        self.pyctuator = Pyctuator(
            self.app,
            "Django Pyctuator",
            f"http://localhost:{self.port}",
            f"http://localhost:{self.port}/pyctuator",
            "http://localhost:8001/register",
            registration_interval_sec=1,
            metadata=self.metadata,
            additional_app_info=self.additional_app_info,
            disabled_endpoints=disabled_endpoints,
        )

    def start(self) -> None:
        logging.info("Starting Django server")
        self.thread.start()
        while True:
            time.sleep(0.5)
            try:
                requests.get(
                    f"http://localhost:{self.port}/pyctuator", timeout=REQUEST_TIMEOUT
                )
                logging.info("Django server started")
                return
            except (
                requests.exceptions.RequestException
            ):  # Catches all exceptions that Requests raises!
                pass

    def stop(self) -> None:
        logging.info("Stopping Django server")
        self.pyctuator.stop()
        self.server.shutdown()
        self.thread.join()

        logging.info("Django server stopped")

    def atexit(self) -> None:
        if self.pyctuator.boot_admin_registration_handler:
            self.pyctuator.boot_admin_registration_handler.deregister_from_admin_server()
