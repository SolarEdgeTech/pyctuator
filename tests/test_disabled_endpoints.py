import logging
from http import HTTPStatus
from typing import Generator

import pytest
import requests

from pyctuator.endpoints import Endpoints
from tests.aiohttp_test_server import AiohttpPyctuatorServer
from tests.conftest import RegisteredEndpoints, PyctuatorServer, endpoint_href_path, REQUEST_TIMEOUT
from tests.fast_api_test_server import FastApiPyctuatorServer
from tests.flask_test_server import FlaskPyctuatorServer
from tests.tornado_test_server import TornadoPyctuatorServer


@pytest.fixture(
    params=[
        Endpoints.THREAD_DUMP | Endpoints.HTTP_TRACE,
        Endpoints.LOGGERS,
        Endpoints.ENV,
        Endpoints.LOGFILE | Endpoints.METRICS | Endpoints.HEALTH,
    ]
)
def disabled_endpoints(request) -> Generator:  # type: ignore
    yield request.param


@pytest.fixture(
    params=[FastApiPyctuatorServer, FlaskPyctuatorServer, TornadoPyctuatorServer, AiohttpPyctuatorServer],
    ids=["FastAPI", "Flask", "Tornado", "AIOHTTP"]
)
def pyctuator_server(disabled_endpoints: Endpoints, request) -> Generator:  # type: ignore
    # Start the web-server in which the pyctuator is integrated
    pyctuator_server: PyctuatorServer = request.param(disabled_endpoints)
    pyctuator_server.start()

    # Yield back to pytest until the module is done
    yield pyctuator_server

    # Once the module is done, stop the pyctuator-server
    pyctuator_server.stop()


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
def test_disabled_endpoints_not_shown(
        disabled_endpoints: Endpoints,
        registered_endpoints: RegisteredEndpoints,
) -> None:
    for endpoint in Endpoints:
        logging.info("Testing that endpoint %s isn't shown in registered endpoints", endpoint)

        registered_endpoint = {
            Endpoints.ENV: registered_endpoints.env,
            Endpoints.INFO: registered_endpoints.info,
            Endpoints.HEALTH: registered_endpoints.health,
            Endpoints.METRICS: registered_endpoints.metrics,
            Endpoints.LOGGERS: registered_endpoints.loggers,
            Endpoints.THREAD_DUMP: registered_endpoints.threads,
            Endpoints.LOGFILE: registered_endpoints.logfile,
            Endpoints.HTTP_TRACE: registered_endpoints.httptrace,
        }.get(endpoint)

        if endpoint in disabled_endpoints:
            assert registered_endpoint is None
        else:
            assert registered_endpoint is not None


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
def test_disabled_endpoints_not_found(
        disabled_endpoints: Endpoints,
        registered_endpoints: RegisteredEndpoints,
) -> None:
    for endpoint in Endpoints:
        if endpoint != Endpoints.NONE and endpoint in disabled_endpoints:
            endpoint_url = f"{registered_endpoints.pyctuator}/{endpoint_href_path.get(endpoint)}"
            logging.info("Testing that disabled-endpoint %s cannot be accessed via %s", endpoint, endpoint_url)
            response = requests.get(endpoint_url, timeout=REQUEST_TIMEOUT)
            assert response.status_code in (HTTPStatus.NOT_FOUND, HTTPStatus.METHOD_NOT_ALLOWED)
