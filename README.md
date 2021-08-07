[![PyPI](https://img.shields.io/pypi/v/pyctuator?color=green&style=plastic)](https://pypi.org/project/pyctuator/)
[![build](https://github.com/SolarEdgeTech/pyctuator/workflows/build/badge.svg)](https://github.com/SolarEdgeTech/pyctuator/)
[![Codecov](https://img.shields.io/codecov/c/github/SolarEdgeTech/pyctuator?style=plastic)](https://codecov.io/gh/SolarEdgeTech/pyctuator)

# Pyctuator

Monitor Python web apps using 
[Spring Boot Admin](https://github.com/codecentric/spring-boot-admin). 

Pyctuator supports **[Flask](https://palletsprojects.com/p/flask/)**, **[FastAPI](https://fastapi.tiangolo.com/)**, **[aiohttp](docs.aiohttp.org)** and **[Tornado](https://www.tornadoweb.org/)**. **Django** support is planned as well.

The following video shows a FastAPI web app being monitored and controled using Spring Boot Admin.
 
![Pyctuator Example](examples/images/Pyctuator_Screencast.gif)

The complete example can be found in [Advanced example](examples/Advanced/README.md).

## Requirements
Python 3.7+

Pyctuator has zero hard dependencies.

## Installing
Install Pyctuator using pip: `pip3 install pyctuator`

## Why?
Many Java shops use Spring Boot as their main web framework for developing
microservices. 
These organizations often use Spring Actuator together with Spring Boot Admin
to monitor their microservices' status, gain access to applications'
 state and configuration, manipulate log levels, etc.
 
While Spring Boot is suitable for many use-cases, it is very common for organizations 
to also have a couple of Python microservices, as Python is often more suitable for 
some types of applications. The most common examples are Data Science and Machine Learning
applications.

Setting up a proper monitoring tool for these microservices is a complex task, and might
not be justified for just a few Python microservices in a sea of Java microservices.

This is where Pyctuator comes in. It allows you to easily integrate your Python
microservices into your existing Spring Boot Admin deployment.

## Main Features
Pyctuator is a partial Python implementation of the 
[Spring Actuator API](https://docs.spring.io/spring-boot/docs/2.1.8.RELEASE/actuator-api/html/)  . 

It currently supports the following Actuator features:

* **Application details**
* **Metrics**
    * Memory usage
    * Disk usage 
    * Custom metrics
* **Health monitors**
    * Built in MySQL health monitor
    * Built in Redis health monitor
    * Custom health monitors
* **Environment**
* **Loggers** - Easily change log levels during runtime
* **Log file** - Tail the application's log file
* **Thread dump** - See which threads are running
* **HTTP traces** - Tail recent HTTP requests, including status codes and latency

## Quickstart
The examples below show a minimal integration of **FastAPI**, **Flask** and **aiohttp** applications with **Pyctuator**.

After installing Flask/FastAPI/aiohttp and Pyctuator, start by launching a local Spring Boot Admin instance:

```sh
docker run --rm --name spring-boot-admin -p 8080:8080 michayaak/spring-boot-admin:2.2.3-1
```

Then go to `http://localhost:8080` to get to the web UI.

### Flask
The following example is complete and should run as is.

```python
from flask import Flask
from pyctuator.pyctuator import Pyctuator

app_name = "Flask App with Pyctuator"
app = Flask(app_name)


@app.route("/")
def hello():
    return "Hello World!"


Pyctuator(
    app,
    app_name,
    app_url="http://host.docker.internal:5000",
    pyctuator_endpoint_url="http://host.docker.internal:5000/pyctuator",
    registration_url="http://localhost:8080/instances"
)

app.run(debug=False, port=5000)
```

The application will automatically register with Spring Boot Admin upon start up.

Log in to the Spring Boot Admin UI at `http://localhost:8080` to interact with the application. 

### FastAPI
The following example is complete and should run as is.

```python
from fastapi import FastAPI
from uvicorn import Server

from uvicorn.config import Config
from pyctuator.pyctuator import Pyctuator


app_name = "FastAPI App with Pyctuator"
app = FastAPI(title=app_name)


@app.get("/")
def hello():
    return "Hello World!"


Pyctuator(
    app,
    "FastAPI Pyctuator",
    app_url="http://host.docker.internal:8000",
    pyctuator_endpoint_url="http://host.docker.internal:8000/pyctuator",
    registration_url="http://localhost:8080/instances"
)

Server(config=(Config(app=app, loop="asyncio"))).run()
```

The application will automatically register with Spring Boot Admin upon start up.

Log in to the Spring Boot Admin UI at `http://localhost:8080` to interact with the application. 

### aiohttp
The following example is complete and should run as is.

```python
from aiohttp import web
from pyctuator.pyctuator import Pyctuator

app = web.Application()
routes = web.RouteTableDef()

@routes.get("/")
def hello():
    return web.Response(text="Hello World!")

Pyctuator(
    app,
    "aiohttp Pyctuator",
    app_url="http://host.docker.internal:8888",
    pyctuator_endpoint_url="http://host.docker.internal:8888/pyctuator",
    registration_url="http://localhost:8080/instances"
)

app.add_routes(routes)
web.run_app(app, port=8888)
```

The application will automatically register with Spring Boot Admin upon start up.

Log in to the Spring Boot Admin UI at `http://localhost:8080` to interact with the application.

### Registration Notes
When registering a service in Spring Boot Admin, note that:
* **Docker** - If the Spring Boot Admin is running in a container while the managed service is running in the docker-host directly, the `app_url` and `pyctuator_endpoint_url` should use `host.docker.internal` as the url's host so Spring Boot Admin will be able to connect to the monitored service.
* **Http Traces** - In order for the "Http Traces" tab to be able to hide requests sent by Spring Boot Admin to the Pyctuator endpoint, `pyctuator_endpoint_url` must be using the same host and port as `app_url`.
* **HTTPS** - If Spring Boot Admin is using HTTPS with self-signed certificate, set the `PYCTUATOR_REGISTRATION_NO_CERT` environment variable so Pyctuator will disable certificate validation when registering (and deregistering).

## Advanced Configuration
The following sections are intended for advanced users who want to configure advanced Pyctuator features.

### Application Info
While Pyctuator only needs to know the application's name, we recommend that applications monitored by Spring 
Boot Admin will show additional build and git details. 
This becomes handy when scaling out a service to multiple instances by showing the version of each instance.
To do so, you can provide additional build and git info using methods of the Pyctuator object:

```python
pyctuator = Pyctuator(...)  # arguments removed for brevity

pyctuator.set_build_info(
    name="app",
    version="1.3.1",
    time=datetime.fromisoformat("2019-12-21T10:09:54.876091"),
)

pyctuator.set_git_info(
    commit="7d4fef3",
    time=datetime.fromisoformat("2019-12-24T14:18:32.123432"),
    branch="origin/master",
)
```

Once you configure build and git info, you should see them in the Details tab of Spring Boot Admin:

![Detailed Build Info](examples/images/Main_Details_BuildInfo.png)

### Additional Application Info
In addition to adding build and git info, Pyctuator allows adding arbitrary application details to the "Info" section in SBA.

This is done by initializing the `additional_app_info` parameter with an arbitrary dictionary.
For example, you can provide links to your application's metrics:
```python
Pyctuator(
  app,
  "Flask Pyctuator",
  app_url=f"http://172.18.0.1:5000",
  pyctuator_endpoint_url=f"http://172.18.0.1:5000/pyctuator",
  registration_url=f"http://localhost:8080/instances",
  app_description="Demonstrate Spring Boot Admin Integration with Flask",
  additional_app_info=dict(
    serviceLinks=dict(
      metrics="http://xyz/service/metrics"
    ),
    podLinks=dict(
      metrics=["http://xyz/pod/metrics/memory", "http://xyz/pod/metrics/cpu"]
    )
  )
)
```

This will result with the following Info page in SBA:
![img.png](examples/images/Additional_App_Info.png)

### DB Health
For services that use SQL database via SQLAlchemy, Pyctuator can easily monitor and expose the connection's health 
using the DbHealthProvider class as demonstrated below:

```python
engine = create_engine("mysql+pymysql://root:root@localhost:3306")
pyctuator = Pyctuator(...)  # arguments removed for brevity
pyctuator.register_health_provider(DbHealthProvider(engine))
```

Once you configure the health provider, you should see DB health info in the Details tab of Spring Boot Admin:

![DB Health](examples/images/Main_DB_Health.png)

### Redis health
If your service is using Redis, Pyctuator can monitor the connection to Redis by simply initializing a `RedisHealthProvider`:

```python
r = redis.Redis()
pyctuator = Pyctuator(...)  # arguments removed for brevity
pyctuator.register_health_provider(RedisHealthProvider(r))
```

### Custom Environment
Out of the box, Pyctuator exposes Python's environment variables to Spring Boot Admin.

In addition, an application may register an environment provider to provide additional configuration that should be exposed via Spring Boot Admin. 

When the environment provider is called it should return a dictionary describing the environment. The returned dictionary is exposed to Spring Boot Admin.

Since Spring Boot Admin doesn't support hierarchical environment (only a flat key/value mapping), the provided environment is flattened as dot-delimited keys.

Pyctuator tries to hide secrets from being exposed to Spring Boot Admin by replacing the values of "suspicious" keys with ***.

Suspicious keys are keys that contain the words "secret", "password" and some forms of "key".

For example, if an application's configuration looks like this:

```python
config = {
    "a": "s1",
    "b": {
        "secret": "ha ha",
        "c": 625,
    },
    "d": {
        "e": True,
        "f": "hello",
        "g": {
            "h": 123,
            "i": "abcde"
        }
    }
}
```

An environment provider can be registered like so:

```python
pyctuator.register_environment_provider("config", lambda: config)
```

### Filesystem and Memory Metrics
Pyctuator can provide filesystem and memory metrics.

To enable these metrics, install [psutil](https://github.com/giampaolo/psutil)

Note that the `psutil` dependency is **optional** and is only required if you want to enable filesystem and memory monitoring.

### Loggers
Pyctuator leverages Python's builtin `logging` framework and allows controlling log levels at runtime.
 
Note that in order to control uvicorn's log level, you need to provide a logger object when instantiating it. For example:
```python
myFastAPIServer = Server(
    config=Config(
        logger=logging.getLogger("uvi"), 
        app=app, 
        loop="asyncio"
    )
)
```

### Spring Boot Admin Using Basic Authentication
Pyctuator supports registration with Spring Boot Admin that requires basic authentications. The credentials are provided when initializing the Pyctuator instance as follows:
```python
# NOTE: Never include secrets in your code !!!
auth = BasicAuth(os.getenv("sba-username"), os.getenv("sba-password"))

Pyctuator(
    app,
    "Flask Pyctuator",
    app_url="http://localhost:5000",
    pyctuator_endpoint_url=f"http://localhost:5000/pyctuator",
    registration_url=f"http://spring-boot-admin:8080/instances",
    registration_auth=auth,
)
``` 

## Full blown examples
The `examples` folder contains full blown Python projects that are built using [Poetry](https://python-poetry.org/).

To run these examples, you'll need to have Spring Boot Admin running in a local docker container. A Spring Boot Admin Docker image is available [here](https://hub.docker.com/r/michayaak/spring-boot-admin).

Unless the example includes a docker-compose file, you'll need to start Spring Boot Admin using docker directly:
```sh
docker run --rm -p 8080:8080 michayaak/spring-boot-admin:2.2.3-1
```
(the docker image's tag represents the version of Spring Boot Admin, so if you need to use version `2.0.0`, use `michayaak/spring-boot-admin:2.0.0` instead, note it accepts connections on port 8082).

The examples include
* [FastAPI Example](examples/FastAPI/README.md) - demonstrates integrating Pyctuator with the FastAPI web framework.
* [Flask Example](examples/Flask/README.md) - demonstrates integrating Pyctuator with the Flask web framework.
* [Advanced Example](examples/Advanced/README.md) - demonstrates configuring and using all the advanced features of Pyctuator.

## Contributing
To set up a development environment, make sure you have Python 3.7 or newer installed, and run `make bootstrap`.

Use `make check` to run static analysis tools.

Use `make test` to run tests.
