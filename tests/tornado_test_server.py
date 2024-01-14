import logging
import threading
import time
from typing import Optional

from tornado import ioloop
from tornado.httpserver import HTTPServer
from tornado.web import Application, RequestHandler

from pyctuator.endpoints import Endpoints
from pyctuator.pyctuator import Pyctuator
from tests.conftest import PyctuatorServer

bind_port = 9000


class TornadoPyctuatorServer(PyctuatorServer):
    def __init__(self, disabled_endpoints: Endpoints = Endpoints.NONE) -> None:
        global bind_port
        self.port = bind_port
        bind_port += 1

        # pylint: disable=abstract-method
        class LogfileTestRepeater(RequestHandler):
            def get(self) -> None:
                repeated_string = self.get_argument("repeated_string")
                logging.error(repeated_string)
                self.write(repeated_string)

        # pylint: disable=abstract-method
        class GetHttptraceTestUrl(RequestHandler):
            def get(self) -> None:
                sleep_sec: Optional[str] = self.get_argument("sleep_sec", None)
                # Sleep if requested to sleep - used for asserting httptraces timing
                if sleep_sec:
                    logging.info(
                        "Sleeping %s seconds before replying", sleep_sec)
                    time.sleep(int(sleep_sec))

                # Echo 'User-Data' header as 'resp-data' - used for asserting headers are captured properly
                self.add_header(
                    "resp-data", str(self.request.headers.get("User-Data")))
                self.add_header(
                    "response-secret", "my password")
                self.write("my content")

        self.app = Application(
            [
                ("/logfile_test_repeater", LogfileTestRepeater),
                ("/httptrace_test_url", GetHttptraceTestUrl)
            ],
            debug=False
        )

        self.pyctuator = Pyctuator(
            self.app,
            "Tornado Pyctuator",
            app_url=f"http://localhost:{self.port}",
            pyctuator_endpoint_url=f"http://localhost:{self.port}/pyctuator",
            registration_url="http://localhost:8001/register",
            app_description="Demonstrate Spring Boot Admin Integration with Tornado",
            registration_interval_sec=1,
            metadata=self.metadata,
            additional_app_info=self.additional_app_info,
            disabled_endpoints=disabled_endpoints,
        )

        self.io_loop: Optional[ioloop.IOLoop] = None
        self.http_server = HTTPServer(self.app, decompress_request=True)
        self.thread = threading.Thread(target=self._start_in_thread)

    def _start_in_thread(self) -> None:
        self.io_loop = ioloop.IOLoop()
        self.app.listen(self.port)
        self.io_loop.start()

    def start(self) -> None:
        logging.info("Starting Tornado server")
        self.thread.start()
        time.sleep(0.5)

    def stop(self) -> None:
        logging.info("Stopping Tornado server")
        self.pyctuator.stop()

        # Allow the recurring registration to complete any in-progress request before stopping Tornado
        time.sleep(1)

        assert self.io_loop is not None

        self.http_server.stop()
        self.io_loop.add_callback(self.io_loop.stop)
        self.thread.join()
        self.io_loop.close(all_fds=True)

    def atexit(self) -> None:
        if self.pyctuator.boot_admin_registration_handler:
            self.pyctuator.boot_admin_registration_handler.deregister_from_admin_server()
