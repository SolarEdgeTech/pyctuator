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


myPyc = Pyctuator(
    app,
    "Example FastAPI",
    "http://localhost:8000",
    "http://localhost:8000/pyctuator",
    "http://localhost:8080/instances",
    app_description=app.description,
    registration_interval_sec=1,
    logfile_max_size=10000,
    logfile_formatter="%(asctime)s  %(levelname)-5s %(process)d -- [%(threadName)s] %(module)s: %(message)s"
)

myFastAPIServer = Server(config=(Config(app=app, loop="asyncio", host="0.0.0.0")))
myFastAPIServer.run()
