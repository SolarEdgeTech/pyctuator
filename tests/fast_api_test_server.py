import logging
import threading
import time

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from uvicorn.config import Config

from pyctuator.pyctuator import Pyctuator
from tests.conftest import PyctuatorServer, CustomServer


class FastApiPyctuatorServer(PyctuatorServer):
    def __init__(self) -> None:
        self.app = FastAPI(
            title="FastAPI Example Server",
            description="Demonstrate Spring Boot Admin Integration with FastAPI",
            docs_url="/api",
        )

        self.pyctuator = Pyctuator(
            self.app,
            "FastAPI Pyctuator",
            "http://localhost:8000",
            "http://localhost:8000/pyctuator",
            "http://localhost:8001/register",
            registration_interval_sec=1,
        )

        @self.app.get("/logfile_test_repeater", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def logfile_test_repeater(repeated_string: str) -> str:
            logging.error(repeated_string)
            return repeated_string

        self.server = CustomServer(config=(Config(app=self.app, loop="asyncio")))
        self.thread = threading.Thread(target=self.server.run)

        @self.app.get("/httptrace_test_url")
        # pylint: disable=unused-variable
        def get_httptrace_test_url(request: Request) -> Response:
            return Response(headers={"header": str(request.headers.get('header'))})

    def start(self) -> None:
        self.thread.start()
        while not self.server.started:
            time.sleep(0.01)

    def stop(self) -> None:
        self.pyctuator.stop()
        self.server.should_exit = True
        self.thread.join()
