import logging
import threading
import time
from wsgiref.simple_server import make_server

import requests
from flask import Flask, request, Response

from pyctuator.pyctuator import Pyctuator
from tests.conftest import PyctuatorServer

REQUEST_TIMEOUT = 10


class FlaskPyctuatorServer(PyctuatorServer):
    def __init__(self) -> None:
        self.app = Flask("Flask Example Server")
        self.server = make_server('127.0.0.1', 5000, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.thread = threading.Thread(target=self.server.serve_forever)

        self.pyctuator = Pyctuator(
            self.app,
            "Flask Pyctuator",
            "http://localhost:5000",
            "http://localhost:5000/pyctuator",
            "http://localhost:8001/register",
            registration_interval_sec=1,
            metadata=self.metadata,
            additional_app_info=self.additional_app_info,
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
                requests.get("http://localhost:5000/pyctuator", timeout=REQUEST_TIMEOUT)
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
