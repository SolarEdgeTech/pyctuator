import asyncio
import logging
import threading
import time
from asyncio.events import AbstractEventLoop
from typing import Optional

from aiohttp import web
from aiohttp.web_runner import AppRunner
from starlette.responses import Response

from pyctuator.pyctuator import Pyctuator
from tests.conftest import PyctuatorServer


# pylint: disable=unused-variable
class AiohttpPyctuatorServer(PyctuatorServer):

    def __init__(self) -> None:
        self.app = web.Application()
        self.routes = web.RouteTableDef()

        self.pyctuator = Pyctuator(
            self.app,
            "AIOHTTP Pyctuator",
            "http://localhost:8888",
            "http://localhost:8888/pyctuator",
            "http://localhost:8001/register",
            registration_interval_sec=1,
        )

        @self.routes.get("/logfile_test_repeater")
        def logfile_test_repeater(request: web.Request) -> web.Response:
            repeated_string = request.query.get("repeated_string")
            logging.error(repeated_string)
            return web.Response(text=repeated_string)

        @self.routes.get("/httptrace_test_url")
        def get_httptrace_test_url(request: web.Request) -> Response:
            # Sleep if requested to sleep - used for asserting httptraces timing
            sleep_sec = request.query.get("sleep_sec")
            if sleep_sec:
                logging.info("Sleeping %s seconds before replying", sleep_sec)
                time.sleep(int(sleep_sec))

            # Echo 'User-Data' header as 'resp-data' - used for asserting headers are captured properly
            return Response(headers={"resp-data": str(request.headers.get("User-Data"))}, content="my content")

        self.app.add_routes(self.routes)
        self.runner: Optional[AppRunner] = None
        self.event_loop: Optional[AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None

    async def _runner(self) -> None:
        self.runner: AppRunner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "localhost", 8888)
        await site.start()

    def start(self) -> None:
        self.event_loop = asyncio.new_event_loop()

        self.event_loop.run_until_complete(self._runner())
        self.thread = threading.Thread(target=lambda: self.event_loop.run_forever())
        self.thread.start()

    def stop(self) -> None:
        self.pyctuator.stop()
        self.event_loop.stop()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.runner.shutdown())
        loop.run_until_complete(self.runner.cleanup())
        self.thread.join()
