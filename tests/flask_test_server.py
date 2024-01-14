import logging
import threading
import time
from wsgiref.simple_server import make_server

import requests
from flask import Flask, request, Response

from pyctuator.endpoints import Endpoints
from pyctuator.pyctuator import Pyctuator
from tests.conftest import PyctuatorServer

REQUEST_TIMEOUT = 10

bind_port = 5000


class FlaskPyctuatorServer(PyctuatorServer):
    def __init__(self, disabled_endpoints: Endpoints = Endpoints.NONE) -> None:
        global bind_port
        self.port = bind_port
        bind_port += 1

        self.app = Flask("Flask Example Server")
        self.server = make_server('127.0.0.1', self.port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.thread = threading.Thread(target=self.server.serve_forever)

        self.pyctuator = Pyctuator(
            self.app,
            "Flask Pyctuator",
            f"http://localhost:{self.port}",
            f"http://localhost:{self.port}/pyctuator",
            "http://localhost:8001/register",
            registration_interval_sec=1,
            metadata=self.metadata,
            additional_app_info=self.additional_app_info,
            disabled_endpoints=disabled_endpoints,
        )

        @self.app.route("/logfile_test_repeater")
        # pylint: disable=unused-variable
        def logfile_test_repeater() -> str:
            repeated_string: str = str(request.args.get("repeated_string"))
            logging.error(repeated_string)
            return repeated_string

        @self.app.route("/httptrace_test_url", methods=["GET"])
        # pylint: disable=unused-variable
        def get_httptrace_test_url() -> Response:
            # Sleep if requested to sleep - used for asserting httptraces timing
            sleep_sec = request.args.get("sleep_sec")
            if sleep_sec:
                logging.info("Sleeping %s seconds before replying", sleep_sec)
                time.sleep(int(sleep_sec))

            # Echo 'User-Data' header as 'resp-data' - used for asserting headers are captured properly
            resp = Response()
            resp.headers["resp-data"] = str(request.headers.get("User-Data"))
            resp.headers["response-secret"] = str(
                request.headers.get("my password"))
            return resp

    def start(self) -> None:
        logging.info("Starting Flask server")
        self.thread.start()
        while True:
            time.sleep(0.5)
            try:
                requests.get(f"http://localhost:{self.port}/pyctuator", timeout=REQUEST_TIMEOUT)
                logging.info("Flask server started")
                return
            except requests.exceptions.RequestException:  # Catches all exceptions that Requests raises!
                pass

    def stop(self) -> None:
        logging.info("Stopping Flask server")
        self.pyctuator.stop()
        self.server.shutdown()
        self.thread.join()
        logging.info("Flask server stopped")

    def atexit(self) -> None:
        if self.pyctuator.boot_admin_registration_handler:
            self.pyctuator.boot_admin_registration_handler.deregister_from_admin_server()
