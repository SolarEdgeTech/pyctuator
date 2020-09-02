import datetime
import logging
import random

from aiohttp import web

from pyctuator.pyctuator import Pyctuator

my_logger = logging.getLogger("example")
app = web.Application()
routes = web.RouteTableDef()


@routes.get('/')
def home(request: web.Request) -> web.Response:
    my_logger.debug(f"{datetime.datetime.now()} - {str(random.randint(0, 100))}")
    print("Printing to STDOUT")
    return web.Response(text="Hello World!")


example_app_address = "host.docker.internal"
example_sba_address = "localhost"

pyctuator = Pyctuator(
    app,
    "Example aiohttp",
    app_url=f"http://{example_app_address}:8888",
    pyctuator_endpoint_url=f"http://{example_app_address}:8888/pyctuator",
    registration_url=f"http://{example_sba_address}:8080/instances",
    app_description="Demonstrate Spring Boot Admin Integration with aiohttp",
)

app.add_routes(routes)
web.run_app(app, port=8888)
