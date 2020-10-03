import datetime
import logging
import random

from tornado import ioloop
from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer

from pyctuator.pyctuator import Pyctuator

my_logger = logging.getLogger("example")

class HomeHandler(RequestHandler):
    def get(self):
        my_logger.debug(f"{datetime.datetime.now()} - {str(random.randint(0, 100))}")
        print("Printing to STDOUT")
        self.write("Hello World!")

app = Application([
    (r"/", HomeHandler)
], debug=False)

example_app_address = "host.docker.internal"
example_sba_address = "localhost"

Pyctuator(
    app,
    "Tornado Pyctuator",
    app_url=f"http://{example_app_address}:5000",
    pyctuator_endpoint_url=f"http://{example_app_address}:5000/pyctuator",
    registration_url=f"http://{example_sba_address}:8080/instances",
    app_description="Demonstrate Spring Boot Admin Integration with Tornado",
)

http_server = HTTPServer(app, decompress_request=True)
http_server.listen(5000)
ioloop.IOLoop.current().start()
