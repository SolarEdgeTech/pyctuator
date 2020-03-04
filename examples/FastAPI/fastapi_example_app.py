import datetime
import logging
import random
import socket

from fastapi import FastAPI
from uvicorn import Server
from uvicorn.config import Config

from pyctuator.pyctuator import Pyctuator

logging.basicConfig(level=logging.INFO)
my_logger = logging.getLogger("example")

app = FastAPI(
    title="FastAPI Example Server",
    description="Demonstrate Spring Boot Admin Integration with FastAPI",
    docs_url="/api",
)


@app.get("/")
def read_root():
    my_logger.debug(f"{datetime.datetime.now()} - {str(random.randint(0, 100))}")
    print("Printing to STDOUT")
    return "Hello World!"


example_app_public_address = socket.gethostbyname(socket.gethostname())
example_app_address_as_seen_from_sba_container = "host.docker.internal"
example_sba_address = "localhost"

pyctuator = Pyctuator(
    app,
    "Example FastAPI",
    f"http://{example_app_public_address}:8000",
    f"http://{example_app_address_as_seen_from_sba_container}:8000/pyctuator",
    f"http://{example_sba_address}:8082/instances",
    app_description=app.description,
)

server = Server(config=(Config(app=app, loop="asyncio", host="0.0.0.0")))
server.run()
