import logging
import threading
import time

import requests
from flask import Flask, request, Response

from pyctuator.pyctuator import Pyctuator
from tests.conftest import PyctuatorServer


class FlaskPyctuatorServer(PyctuatorServer):
    def __init__(self) -> None:
        self.app = Flask("Flask Example Server")
        self.thread = threading.Thread(target=self.app.run)

        self.pyctuator = Pyctuator(
            self.app,
            "Flask Pyctuator",
            "http://localhost:5000",
            "http://localhost:5000/pyctuator",
            "http://localhost:8001/register",
            registration_interval_sec=1
        )

        @self.app.route("/shutdown", methods=["POST"])
        # pylint: disable=unused-variable
        def shutdown() -> str:
            logging.info("Flask server shutting down...")
            func = request.environ.get("werkzeug.server.shutdown")
            if func is None:
                raise RuntimeError("Not running with the Werkzeug Server")
            func()
            return "Flask server off"

        @self.app.route("/logfile_test_repeater")
        # pylint: disable=unused-variable
        def logfile_test_repeater() -> str:
            repeated_string: str = str(request.args.get('repeated_string'))
            logging.error(repeated_string)
            return repeated_string

        @self.app.route("/httptrace_test_url", methods=["GET"])
        # pylint: disable=unused-variable
        def get_httptrace_test_url() -> Response:
            resp = Response()
            resp.headers["Resp-Data"] = str(request.headers.get('User-Data'))
            return resp

    def start(self) -> None:
        self.thread.start()
        while True:
            time.sleep(0.5)
            try:
                requests.get("http://localhost:5000/pyctuator")
                return
            except requests.exceptions.RequestException:  # Catches all exceptions that Requests raises!
                pass

    def stop(self) -> None:
        self.pyctuator.stop()
        requests.post("http://localhost:5000/shutdown")
        self.thread.join()
