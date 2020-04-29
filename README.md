![build](https://github.com/yanoom/pyctuator/workflows/build/badge.svg)
![codecov](https://codecov.io/gh/yanoom/pyctuator/branch/master/graph/badge.svg)

# Pyctuator

Monitoring your Python microservices as if they were Spring
Boot applications using 
[Spring Boot Admin](https://github.com/codecentric/spring-boot-admin). 

The supported web frameworks are **Flask** and **FastAPI**.

Support for **Django** is planned as well.

The following video shows Spring Boot Admin to monitoring and controlling an instance of the [Advanced example](examples/Advanced/README.md):
![Pyctuator Example](examples/images/Pyctuator_Screencast.gif)

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
 
These organizations often have the occasional Python microservice, especially as
Python Machine Learning and Data Science packages gain popularity. Setting up
a proper monitoring tool for these microservices is a complex task, and might
not be justified for a few Python microservices in a sea of Java microservices.

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
    * Easily add custom metrics
* **Health monitors**
    * Built in MySQL health monitor
    * Built in Redis health monitor
    * Easily add custom health monitors
* **Environment**
* **Loggers** - Easily change log levels during runtime
* **Log file** - Tail the application's log file
* **Thread dump** - See which threads are running
* **HTTP traces** - Tail recent HTTP requests, including status codes and latency

## Quickstart
The examples below show a minimal integration of **FastAPI** and **Flask** applications with **Pyctuator**.

After installing Flask/FastAPI and Pyctuator, start by launching a local Spring Boot Admin instance:

```sh
docker run --rm --name spring-boot-admin -p 8082:8082 michayaak/spring-boot-admin:2.2.2
```

Then go to `http://localhost:8082` to get to the web UI.

### Flask
The following is a complete example and should run as is:

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
    "http://host.docker.internal:5000",
    "http://host.docker.internal:5000/pyctuator",
    "http://localhost:8082/instances"
)

app.run(debug=False, port=5000)
```

Once you run the application, it should automatically register with Spring Boot Admin and should be available in the UI at `http://localhost:8082`

### FastAPI
The following is a complete example and should run as is:

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
    "http://host.docker.internal:8000",
    "http://host.docker.internal:8000/pyctuator",
    "http://localhost:8080/instances"
)

Server(config=(Config(app=app, loop="asyncio"))).run()
```


Once you run the application, it should automatically register with Spring Boot Admin and should be available in the UI at `http://localhost:8082`

## Advanced Configuration
The following sections are intended for advanced users who want to configure advanced Pyctuator features.

### Application Info
While Pyctuator only needs to know the application's name, it is recommended that applications monitored by Spring 
Boot Admin will show additional build and git details - this becomes handy when a service is scaled out to multiple instances by showing the version of each instance.
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

## Full blown examples
The `examples` folder contains full blown Python projects that are built using [Poetry](https://python-poetry.org/).

To run these examples, you'll need to have Spring Boot Admin running in a local docker container. A Spring Boot Admin Docker image is available [here](https://hub.docker.com/r/michayaak/spring-boot-admin).

Unless the example includes a docker-compose file, you'll need to start Spring Boot Admin using docker directly:
```sh
docker run -p 8082:8082 michayaak/spring-boot-admin:2.2.2
```
(the docker image's tag represents the version of Spring Boot Admin, so if you need to use version `2.0.0`, use `michayaak/spring-boot-admin:2.0.0` instead).

The examples include
* [FastAPI Example](examples/FastAPI/README.md) - demonstrates integrating Pyctuator with the FastAPI web framework.
* [Flask Example](examples/Flask/README.md) - demonstrates integrating Pyctuator with the Flask web framework.
* [Advanced Example](examples/Advanced/README.md) - demonstrates configuring and using all the advanced features of Pyctuator.

## Contributing
To set up a development environment, make sure you have Python 3.7 or newer installed, and run `make bootstrap`.

Use `make check` to run static analysis tools.

Use `make test` to run tests.
