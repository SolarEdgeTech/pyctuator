import importlib.util
import json
import logging
import os
import random
import time
from dataclasses import dataclass, asdict, fields
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Generator, List

import pytest
import requests
from _pytest.monkeypatch import MonkeyPatch
from requests import Response

from pyctuator.impl import SBA_V2_CONTENT_TYPE
from tests.aiohttp_test_server import AiohttpPyctuatorServer
from tests.conftest import Endpoints, PyctuatorServer, RegistrationRequest, RegistrationTrackerFixture
from tests.fast_api_test_server import FastApiPyctuatorServer
from tests.flask_test_server import FlaskPyctuatorServer


# mypy: ignore_errors
@pytest.fixture(
    params=[FastApiPyctuatorServer, FlaskPyctuatorServer, AiohttpPyctuatorServer],
    ids=["FastAPI", "Flask", "aiohttp"]
)
def pyctuator_server(request) -> Generator:  # type: ignore
    # Start a the web-server in which the pyctuator is integrated
    pyctuator_server: PyctuatorServer = request.param()
    pyctuator_server.start()

    # Yield back to pytest until the module is done
    yield None

    # Once the module is done, stop the pyctuator-server
    pyctuator_server.stop()


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_self_endpoint
def test_response_content_type(endpoints: Endpoints, registration_tracker: RegistrationTrackerFixture) -> None:
    # Issue requests to all actuator endpoints and verify the correct content-type is returned
    actuator_endpoint_names = [field.name for field in fields(Endpoints) if field.name != "root"]
    for actuator_endpoint in actuator_endpoint_names:
        actuator_endpoint_url = asdict(endpoints)[actuator_endpoint]
        logging.info("Testing content type of %s (%s)", actuator_endpoint, actuator_endpoint_url)
        response = requests.get(actuator_endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers.get("Content-Type", response.headers.get("content-type")) == SBA_V2_CONTENT_TYPE

    # Issue requests to non-actuator endpoints and verify the correct content-type is returned
    assert registration_tracker.registration
    for non_actuator_endpoint_url in ["/", "/httptrace_test_url"]:
        non_actuator_endpoint_url = registration_tracker.registration.serviceUrl[:-1] + non_actuator_endpoint_url
        response = requests.get(non_actuator_endpoint_url)
        content_type = response.headers.get("Content-Type", response.headers.get("content-type"))
        logging.info("Testing content type, %s from request %s", content_type, non_actuator_endpoint_url)
        assert not content_type or content_type.find(SBA_V2_CONTENT_TYPE) == -1

    # Finally, verify the  content-type headers presented by the httptraces are correct
    traces = requests.get(endpoints.httptrace).json()["traces"]
    for trace in traces:
        request_uri = trace["request"]["uri"]
        response_headers = trace["response"]["headers"]
        content_type_header: List[str] = response_headers.get("content-type", response_headers.get("Content-Type", []))

        logging.info("Testing httptraces content-type header for request %s, got %s", request_uri, content_type_header)

        if request_uri.find("/pyctuator") > 0:
            assert any(SBA_V2_CONTENT_TYPE in ct for ct in content_type_header)
        else:
            assert all(SBA_V2_CONTENT_TYPE not in ct for ct in content_type_header)


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_self_endpoint
def test_self_endpoint(endpoints: Endpoints) -> None:
    response = requests.get(endpoints.pyctuator)
    assert response.status_code == HTTPStatus.OK
    assert response.json()["_links"] is not None


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_env_endpoint
def test_env_endpoint(endpoints: Endpoints) -> None:
    actual_key, actual_value = list(os.environ.items())[3]
    response = requests.get(endpoints.env)
    assert response.status_code == HTTPStatus.OK
    property_sources = response.json()["propertySources"]
    assert property_sources
    system_properties = [source for source in property_sources if source["name"] == "systemEnvironment"]
    assert system_properties
    assert system_properties[0]["properties"][actual_key]["value"] == actual_value

    response = requests.get(endpoints.info)
    assert response.status_code == HTTPStatus.OK
    assert response.json()["app"] is not None


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_builtin_health_endpoint
def test_health_endpoint_with_psutil(endpoints: Endpoints, monkeypatch: MonkeyPatch) -> None:
    # Skip this test if psutil isn't installed
    psutil = pytest.importorskip("psutil")

    # Verify that the diskSpace health check is returning some reasonable values
    response = requests.get(endpoints.health)
    assert response.status_code == HTTPStatus.OK
    assert response.json()["status"] == "UP"
    disk_space_health = response.json()["details"]["diskSpace"]
    assert disk_space_health["status"] == "UP"
    assert disk_space_health["details"]["free"] > 110000000

    # Now mock the results of psutil so it'll show very small amount of free space
    @dataclass
    class MockDiskUsage:
        total: int
        free: int

    def mock_disk_usage(path: str) -> MockDiskUsage:
        # pylint: disable=unused-argument
        return MockDiskUsage(100000000, 9999999)

    monkeypatch.setattr(psutil, "disk_usage", mock_disk_usage)
    response = requests.get(endpoints.health)
    assert response.status_code == HTTPStatus.OK
    assert response.json()["status"] == "DOWN"
    disk_space_health = response.json()["details"]["diskSpace"]
    assert disk_space_health["status"] == "DOWN"
    assert disk_space_health["details"]["free"] == 9999999
    assert disk_space_health["details"]["total"] == 100000000


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_builtin_health_endpoint
def test_diskspace_no_psutil(endpoints: Endpoints) -> None:
    # skip if psutil is installed
    if importlib.util.find_spec("psutil"):
        pytest.skip("psutil installed, skipping")

    # Verify that the diskSpace health check is returning some reasonable values
    response = requests.get(endpoints.health)
    assert response.status_code == HTTPStatus.OK
    assert response.json()["status"] == "UP"
    assert "diskSpace" not in response.json()["details"]


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_metrics_endpoint
def test_metrics_endpoint(endpoints: Endpoints) -> None:
    # Skip this test if psutil isn't installed
    pytest.importorskip("psutil")

    response = requests.get(endpoints.metrics)
    assert response.status_code == HTTPStatus.OK
    metric_names = response.json()["names"]
    assert "memory.rss" in metric_names
    assert "thread.count" in metric_names

    response = requests.get(f"{endpoints.metrics}/memory.rss")
    assert response.status_code == HTTPStatus.OK
    metric_json = response.json()
    assert metric_json["name"] == "memory.rss"
    assert metric_json["measurements"][0]["statistic"] == "VALUE"
    assert metric_json["measurements"][0]["value"] > 10000

    response = requests.get(f"{endpoints.metrics}/thread.count")
    assert response.status_code == HTTPStatus.OK
    metric_json = response.json()
    assert metric_json["name"] == "thread.count"
    assert metric_json["measurements"][0]["statistic"] == "COUNT"
    assert metric_json["measurements"][0]["value"] > 8


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_recurring_registration
def test_recurring_registration(registration_tracker: RegistrationTrackerFixture) -> None:
    # Verify that at least 4 registrations occurred within 10 seconds since the test started
    start = time.time()
    while registration_tracker.count < 4:
        time.sleep(0.5)
        if time.time() - start > 15:
            pytest.fail(
                f"Expected at least 4 recurring registrations within 10 seconds but got {registration_tracker.count}")

    # Verify that the reported startup time is the same across all the registrations and that its later then the test's
    # start time
    assert isinstance(registration_tracker.registration, RegistrationRequest)
    assert registration_tracker.start_time == registration_tracker.registration.metadata["startup"]
    registration_start_time = datetime.fromisoformat(registration_tracker.start_time)
    assert registration_start_time > registration_tracker.test_start_time - timedelta(seconds=10)


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_threads_endpoint
def test_threads_endpoint(endpoints: Endpoints) -> None:
    response = requests.get(endpoints.threads)
    assert response.status_code == 200

    threads = response.json()["threads"]
    assert len(threads) > 5

    main_thread_list = [t for t in threads if t["threadName"] == "MainThread"]
    assert len(main_thread_list) == 1

    stack = main_thread_list[0]["stackTrace"]
    test_stack_entries = [s for s in stack if s["fileName"] == "test_pyctuator_e2e.py"]
    current_test_stack_entry = [t for t in test_stack_entries if t["methodName"] == "test_threads_endpoint"]
    assert len(current_test_stack_entry) == 1


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_loggers_endpoint
def test_loggers_endpoint(endpoints: Endpoints) -> None:
    response = requests.get(endpoints.loggers)
    assert response.status_code == HTTPStatus.OK

    # levels section
    loggers_levels = response.json()["levels"]
    assert "ERROR" in loggers_levels
    assert "INFO" in loggers_levels
    assert "WARN" in loggers_levels
    assert "DEBUG" in loggers_levels
    # logger names section
    loggers_dict = response.json()["loggers"]
    assert len(loggers_dict) >= 0
    for logger in loggers_dict:
        logger_obj = logging.getLogger(logger)
        assert hasattr(logger_obj, "level")
        # Individual Get logger route
        response = requests.get(f"{endpoints.loggers}/{logger}")
        assert response.status_code == HTTPStatus.OK
        assert "configuredLevel" in json.loads(response.content)
        assert "effectiveLevel" in json.loads(response.content)
        # Set logger level
        if logger in ["uvicorn", ]:  # Skip uvicorn set test, see comment in README.md
            continue

        current_log_level = json.loads(response.content)["configuredLevel"]
        other_log_levels = [level for level in loggers_levels if level is not current_log_level]
        random_log_level = random.choice(other_log_levels)
        post_data = json.dumps({"configuredLevel": str(random_log_level)})

        response = requests.post(f"{endpoints.loggers}/{logger}",
                                 data=post_data)
        assert response.status_code == HTTPStatus.OK
        # Perform get logger level to Validate set logger level succeeded
        response = requests.get(f"{endpoints.loggers}/{logger}")
        assert json.loads(response.content)["configuredLevel"] == random_log_level


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_logfile
def test_logfile_endpoint(endpoints: Endpoints) -> None:
    thirsty_str = "These pretzels are making me thirsty"
    response: Response = requests.get(
        endpoints.root + "logfile_test_repeater",
        params={"repeated_string": thirsty_str}
    )
    assert response.status_code == HTTPStatus.OK

    response = requests.get(endpoints.logfile)
    assert response.status_code == HTTPStatus.OK
    assert response.text.find(thirsty_str) >= 0

    response = requests.get(endpoints.logfile, headers={"Range": "bytes=-307200"})  # Immitate SBA's 1st request
    assert response.status_code == HTTPStatus.PARTIAL_CONTENT


@pytest.mark.usefixtures("boot_admin_server", "pyctuator_server")
@pytest.mark.mark_traces_endpoint
def test_traces_endpoint(endpoints: Endpoints) -> None:
    response = requests.get(endpoints.httptrace)
    assert response.status_code == 200

    # Create a request with header
    user_header = "my header test"
    requests.get(endpoints.root + "httptrace_test_url", headers={"User-Data": user_header})

    # Get the captured httptraces
    response = requests.get(endpoints.httptrace)
    response_traces = response.json()["traces"]
    trace = next(x for x in response_traces if x["request"]["uri"].endswith("httptrace_test_url"))

    # Assert header appears on httptrace url
    assert user_header == trace["response"]["headers"]["resp-data"][0]
    assert int(response.headers.get("Content-Length", -1)) > 0

    # Assert timestamp is formatted in ISO format
    datetime.fromisoformat(trace["timestamp"])

    # Assert that the "time taken" (i.e. the time the server spent processing the request) is less than 100ms
    assert int(trace["timeTaken"]) < 100

    # Issue the same request asking the server to sleep for a sec, than assert request timing is at least 1s
    requests.get(endpoints.root + "httptrace_test_url", params={"sleep_sec": 1}, headers={"User-Data": user_header})
    response = requests.get(endpoints.httptrace)
    response_traces = response.json()["traces"]
    trace = next(x for x in response_traces if "httptrace_test_url?sleep_sec" in x["request"]["uri"])
    assert int(trace["timeTaken"]) > 1000
