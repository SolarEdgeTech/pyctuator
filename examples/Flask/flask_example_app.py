import datetime
import logging
import random
import socket

from flask import Flask

from pyctuator.pyctuator import Pyctuator

logging.basicConfig(level=logging.INFO)

my_logger = logging.getLogger("example")

app = Flask("Flask Example Server")


@app.route("/")
def hello():
    my_logger.debug(f"{datetime.datetime.now()} - {str(random.randint(0, 100))}")
    print("Printing to STDOUT")
    return "Hello World!"


example_app_public_address = socket.gethostbyname(socket.gethostname())
example_app_address_as_seen_from_sba_container = "host.docker.internal"
example_sba_address = "localhost"

Pyctuator(
    app,
    "Flask Pyctuator",
    f"http://{example_app_public_address}:5000",
    f"http://{example_app_address_as_seen_from_sba_container}:5000/pyctuator",
    f"http://{example_sba_address}:8082/instances",
    app_description="Demonstrate Spring Boot Admin Integration with Flask",
    registration_interval_sec=100,
    logfile_max_size=10000,
    logfile_formatter="%(asctime)s  %(levelname)-5s %(process)d -- [%(threadName)s] %(module)s: %(message)s"
)

app.run(port=5000, host="0.0.0.0")
