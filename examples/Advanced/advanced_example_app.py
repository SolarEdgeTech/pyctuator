import datetime
import logging
import random
import socket
from dataclasses import dataclass
from typing import Any, Dict, List
from starlette.requests import Request

import redis
from fastapi import FastAPI
from sqlalchemy.engine import Engine, create_engine
from uvicorn import Server
from uvicorn.config import Config

from pyctuator.health.db_health_provider import DbHealthProvider
from pyctuator.health.health_provider import HealthProvider, HealthStatus, Status, HealthDetails
from pyctuator.health.redis_health_provider import RedisHealthProvider
from pyctuator.pyctuator import Pyctuator

# ----------------------------------------------------------------------------------------------------------------------
# The `app_config` variable below holds all the settings of the application which in addition for being used by the
# application, is also exposed to SBA (after scrubbing secrets) through Pyctuator.
# ----------------------------------------------------------------------------------------------------------------------

app_config = {
    "app": {
        "name": "Advanced Example Server",
        "version": "1.3.1",
        "build_time": datetime.datetime.fromisoformat("2019-12-21T10:09:54.876091"),
        "description": "Demonstrate Spring Boot Admin Integration with FastAPI",

        "git": {
            "commit": "7d4fef3",
            "time": datetime.datetime.fromisoformat("2019-12-24T14:18:32.123432"),
            "branch": "master",
        },

        # the URL to use when accessing the application
        "public_endpoint": f"http://{socket.gethostbyname(socket.gethostname())}:8000",
    },
    "mysql": {
        "host": "localhost:3306",
        "user": "root",

        # NOTE: don't put secrets in code, get them from env! (although Pyctuator will scrub this)
        "password": "root",
    },
    "monitoring": {
        # Because SBA runs in a container, this is the URL of the app/pyctuator as seen from the SBA container
        "pyctuator_endpoint": f"http://host.docker.internal:8000/pyctuator",

        # Spring Boot Admin registration URL
        "sba_registration_endpoint": f"http://localhost:8082/instances",
    }
}


def get_conf(key: str) -> Any:
    def recursive_get(child_conf: Dict, key_parts: List[str]) -> Any:
        if len(key_parts) == 1:
            return child_conf[key_parts[0]]
        return recursive_get(child_conf[key_parts[0]], key_parts[1:])

    return recursive_get(app_config, key.split("."))


# ----------------------------------------------------------------------------------------------------------------------
# A FastAPI application is initialized providing some test API
# ----------------------------------------------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExampleApp")

# Initialize a connection to the DB which the app is using
db_engine: Engine = create_engine(
    "mysql+pymysql://{user}:{password}@{host}".format(
        user=get_conf("mysql.user"),
        password=get_conf("mysql.password"),
        host=get_conf("mysql.host"),
    ),
    echo=True)

# Initialize a redis client for the app to use
redis_client = redis.Redis()

app = FastAPI(
    title=get_conf("app.name"),
    description=get_conf("app.description"),
    docs_url="/api",
)


@dataclass
class AppSpecificHealthDetails(HealthDetails):
    backend_connectivity: str
    available_resources: int


app_specific_health = HealthStatus(
    status=Status.UP,
    details=AppSpecificHealthDetails(backend_connectivity="Connected", available_resources=35)
)


@app.get("/")
def hello():
    logger.debug(f"{datetime.datetime.now()} - {str(random.randint(0, 100))}")
    print("Printing to STDOUT")
    return "Hello World!"


@app.get("/redis/{key}")
def redis_get(key: str) -> Any:
    return redis_client.get(key)


@app.get("/db/version")
def db_version() -> Any:
    return db_engine.execute("SELECT version()").next()[0]


@app.post("/health")
def health_up(request: Request, health: Dict) -> None:  # health should be of type HealthStatus
    global app_specific_health
    app_specific_health = HealthStatus(Status[health["status"]], details=health["details"])


# ----------------------------------------------------------------------------------------------------------------------
# Initialize Pyctuator with the SBA endpoint and all the extensions
# ----------------------------------------------------------------------------------------------------------------------

pyctuator = Pyctuator(
    app,
    get_conf("app.name"),
    get_conf("app.public_endpoint"),
    get_conf("monitoring.pyctuator_endpoint"),
    get_conf("monitoring.sba_registration_endpoint"),
    app_description=app.description,
)

# Provide app's build info
pyctuator.set_build_info(
    name=get_conf("app.name"),
    version=get_conf("app.version"),
    time=get_conf("app.build_time"),
)

# Provide git commit info
pyctuator.set_git_info(
    commit=get_conf("app.git.commit"),
    time=get_conf("app.git.time"),
    branch=get_conf("app.git.branch"),
)

# Expose app's config via the Pyctuator API for SBA to show the scrubbed version in the UI
pyctuator.register_environment_provider("conf", lambda: app_config)

# Add health check for the DB connection
pyctuator.register_health_provider(DbHealthProvider(db_engine))

# Add health check for the Redis client
pyctuator.register_health_provider(RedisHealthProvider(redis_client))


# Register a custom health provider that reflects the contents of `healthy` and `health_details` to SBA
class CustomHealthProvider(HealthProvider):

    def is_supported(self) -> bool:
        return True

    def get_name(self) -> str:
        return "app-specific-health"

    def get_health(self) -> HealthStatus:
        return app_specific_health


pyctuator.register_health_provider(CustomHealthProvider())

# ----------------------------------------------------------------------------------------------------------------------
# The server is started after Pyctuator is created to allow Pyctuator to fully integrate with FastAPI
# ----------------------------------------------------------------------------------------------------------------------
server = Server(config=(Config(app=app, loop="asyncio", host="0.0.0.0")))
server.run()
