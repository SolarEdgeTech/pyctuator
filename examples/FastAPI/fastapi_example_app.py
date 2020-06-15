import datetime
import logging
import random

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


example_app_address = "host.docker.internal"
example_sba_address = "localhost"

pyctuator = Pyctuator(
    app,
    "Example FastAPI",
    app_url=f"http://{example_app_address}:8000",
    pyctuator_endpoint_url=f"http://{example_app_address}:8000/pyctuator",
    registration_url=f"http://{example_sba_address}:8080/instances",
    app_description=app.description,
)

# Keep the console clear - configure uvicorn (FastAPI's WSGI web app) not to log the detail of every incoming request
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.WARNING)

server = Server(config=(Config(
    app=app,
    loop="asyncio",
    host="0.0.0.0",
    logger=uvicorn_logger,
)))
server.run()
