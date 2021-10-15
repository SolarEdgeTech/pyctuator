import datetime
import logging
import random
import secrets

from fastapi import FastAPI, Depends, APIRouter, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from starlette import status
from uvicorn import Server
from uvicorn.config import Config

from pyctuator.pyctuator import Pyctuator

my_logger = logging.getLogger("example")


class SimplisticBasicAuth:
    def __init__(self, username: str, password: str):
        """
        Initializes a simplistic basic-auth FastAPI dependency with hardcoded username and password -
        don't do this at home!
        """
        self.username = username
        self.password = password

    def __call__(self, credentials: HTTPBasicCredentials = Depends(HTTPBasic(realm="pyctuator"))):
        correct_username = secrets.compare_digest(credentials.username, self.username)
        correct_password = secrets.compare_digest(credentials.password, self.password) if self.password else True

        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )


username = "u1"
password = "p2"
security = SimplisticBasicAuth(username, password)


app = FastAPI(
    title="FastAPI Example Server",
    description="Demonstrate Spring Boot Admin Integration with FastAPI",
    docs_url="/api",
)


def add_authentication_to_pyctuator(router: APIRouter) -> None:
    router.dependencies = [Depends(security)]


@app.get("/")
def read_root(credentials: HTTPBasicCredentials = Depends(security)):
    my_logger.debug(f"{datetime.datetime.now()} - {str(random.randint(0, 100))}")
    return {"username": credentials.username, "password": credentials.password}


example_app_address = "172.18.0.1"
example_sba_address = "localhost"

pyctuator = Pyctuator(
    app,
    "Example FastAPI",
    app_url=f"http://{example_app_address}:8000",
    pyctuator_endpoint_url=f"http://{example_app_address}:8000/pyctuator",
    registration_url=f"http://{example_sba_address}:8080/instances",
    app_description=app.description,
    customizer=add_authentication_to_pyctuator,  # Customize Pyctuator's API router to require authentication
    metadata={
        "user.name": username,  # Include the credentials in the registration request sent to SBA
        "user.password": password,
    }
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
