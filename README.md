# Pyctuator

Pyctuator is a Python implementation of the Spring Actuator API for popular web frameworks,  
which allows a web application written in Python to be managed and monitored by codecentric's
[Spring Boot Admin](https://github.com/codecentric/spring-boot-admin).  
Pyctuator implements a growing subset of the actuator API   
(see https://docs.spring.io/spring-boot/docs/2.1.8.RELEASE/actuator-api/html/)  
that allows monitoring Python applications using Spring Boot Admin.

## Why?

## Quickstart

## Configuration
### Application Info
While Pyctuator only require to know the application's name, it is recommended that applications monitored by Spring 
Boot Admin will show additional build and git details - this becomes handy when a service is scaled out with multiple 
instances by showing the version of each instance.
To do so, you can provide additional build and git info using methods of the Pyctuator object:
```python
pyctuator = Pyctuator(
    app,
    "Pyctuator",
    "http://my-micro-service:8000",
    "http://my-micro-service:8000/pyctuator",
    "http://spring-boot-admin:8082/instances",
    app_description="An example application that is managed by Spring Boot Admin",
)

pyctuator.set_build_info(
    name="app",
    version="1.3.1",
    time=datetime.fromisoformat("2019-12-21T10:09:54.876091"),
)
pyctuator.set_git_info(
    commit="7d4fef3",
    time=datetime.fromisoformat("2019-12-24T14:18:32.123432"),
    branch="origin/branch",
)
```
This results with the following:
![Pyctuator](/uploads/7194d2657ab769cda2a12e516d789da4/image.png)

### DB Health
For services that using SQL database via SQLAlchemy, Pyctuator can easily monitor and expose the connection's health 
using the DbHealthProvider class as demonstrated below:
```python
engine: Engine = create_engine("mysql+pymysql://root:root@localhost:3306", echo=True)
pyctuator = Pyctuator(...)
pyctuator.register_health_provider(DbHealthProvider(engine))
```
When the DB is up and running, the health API returns:
```json
{
  "status": "UP",
  "details": {
    "diskSpace": {
      "status": "UP",
      "details": {
        "total": 506333229056,
        "free": 332432617472,
        "threshold": 104857600
      }
    },
    "db": {
      "status": "UP",
      "details": {
        "engine": "mysql",
        "failure": null
      }
    }
  }
}
```
However, when the DB is offline (or any other failure), the health API will return:
```json
{
  "status": "DOWN",
  "details": {
    "diskSpace": {
      "status": "UP",
      "details": {
        "total": 506333229056,
        "free": 332507475968,
        "threshold": 104857600
      }
    },
    "db": {
      "status": "DOWN",
      "details": {
        "engine": "mysql",
        "failure": "(pymysql.err.OperationalError) (2013, 'Lost connection to MySQL server during query')\n[SQL: SELECT 1577567795140]\n(Background on this error at: http://sqlalche.me/e/e3q8)"
      }
    }
  }
}
``` 

### Redis health
If your service is using Redis, Pyctuator can monitor the connection to redis by simply initializing a 
`RedisHealthProvider`:
```python
r = redis.Redis()
pyctuator = Pyctuator(...)
pyctuator.register_health_provider(RedisHealthProvider(r))
```

### Custom Environment
Out of the box, Pyctuator is exposing python's environment variables to Spring Boot Admin. In addition, an application 
may register an environment-provider which when called, returns a dictionary that may contain primitives and other 
dictionaries, which is then exposed to Spring Boot Admin.

Since Spring Boot Admin doesn't support hierarchical environment (only a flat key/value mapping), the provided 
environment is flattened as dot-delimited keys.

Also, Pyctuator tries to hide/scrub secrets from being exposed to Spring Boot Admin by replacing values that their 
keys hit they are secrets (i.e. containing the words "secret", "password" and some forms of "key").

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
And an environment provider was registered like this:
```python
pyctuator.register_environment_provider("conf", lambda: conf)
```
Then calling on http://localhost:8080/pyctuator/env will return:
```JSON
{
  "activeProfiles": [],
  "propertySources": [
    {
      "name": "systemEnvironment",
      "properties": {
        "COMPUTERNAME": {
          "value": "SERVER-X",
          "origin": null
        },
        "NUMBER_OF_PROCESSORS": {
          "value": "8",
          "origin": null
        },
        "OS": {
          "value": "Windows_NT",
          "origin": null
        },
        "PROMPT": {
          "value": "(pyctuator-py3.7) $P$G",
          "origin": null
        },
        "USERNAME": {
          "value": "Joe",
          "origin": null
        },
      }
    },
    {
      "name": "conf",
      "properties": {
        "a": {
          "value": "s1",
          "origin": null
        },
        "b.secret": {
          "value": "******",
          "origin": null
        },
        "b.c": {
          "value": 625,
          "origin": null
        },
        "d.e": {
          "value": true,
          "origin": null
        },
        "d.f": {
          "value": "hello",
          "origin": null
        },
        "d.g.h": {
          "value": 123,
          "origin": null
        },
        "d.g.i": {
          "value": "abcde",
          "origin": null
        }
      }
    }
  ]
}
```
## Examples
The examples below show how to integrate Pyctuator with applications built using FastAPI and Flask.
### Flask
```python
from flask import Flask

from pyctuator.pyctuator import Pyctuator

myFlaskApp = Flask("ExampleFlaskApp")


@myFlaskApp.route("/")
def hello():
    return "Hello World!"


Pyctuator(
    myFlaskApp,
    "Flask Pyctuator",
    "http://localhost:5000",
    "http://localhost:5000/pyctuator",
    "http://localhost:8080/instances"
)

myFlaskApp.run(debug=False, port=5000)

```
### FastAPI
```python
from fastapi import FastAPI
from uvicorn import Server

from uvicorn.config import Config
from pyctuator.pyctuator import Pyctuator


app = FastAPI(
    title="FastAPI Example Server",
    description="Demonstrate Spring Boot Admin Integration with FastAPI",
    docs_url="/api",
)


@app.get("/")
def read_root():
    return "Hello World!"


Pyctuator(
    app,
    "FastAPI Pyctuator",
    "http://localhost:8000",
    "http://localhost:8000/pyctuator",
    "http://localhost:8080/instances"
)

myFastAPIServer = Server(config=(Config(app=app, loop="asyncio")))
myFastAPIServer.run()

```

### Full blown examples
The `examples` folder contains full blown Python projects that are built using Poetry from https://python-poetry.org/.
These examples assume you are running Spring Boot Admin in a docker container which is available from https://hub.docker.com/r/michayaak/spring-boot-admin.

To start Spring Boot Admin version 2.2.2 issue the following command:
```shell script
docker run -p 8082:8082 michayaak/spring-boot-admin:2.2.2
```
The docker image tag represents the version of Spring Boot Admin, so if you need to use version `2.0.0`, issue the
 following command instead: 
```shell script
docker run -p 8082:8082 michayaak/spring-boot-admin:2.0.0
```

Once Spring Boot Admin is running, you can run the examples as follow:
```shell script
cd examples/FastAPI
poetry install
poetry run python -m fastapi_example_app
``` 

## Usage notes
### Using psutil for process/filesystem metrics
In order for pyctuator to provide process/filesystem metrics, it is using the *optional* `psutil` library from:  
https://github.com/giampaolo/psutil  
(if the library isn't available in a system using the pyctuator, pyctuator will not provide such metrics). 
### When using uvicorn
* In order to control the log level of uvicorn, when instantiating, you need to provide a logger object.
Start uvicorn with `logger` object, for example:   
`myFastAPIServer = Server(
    config=Config(
        logger=logging.getLogger("uvi"), 
        app=app, 
        loop="asyncio"
    )
)`

## Contributing
To set up a development environment, make sure you have Python 3.7 or newer installed, and execute `make bootstrap`.

Use `make check` to run static analysis tools.

Use `make test` to run tests.

### Design document
![Pyctuator](/uploads/8183be2327a2703be14a628d484b8a4b/Pyctuator.JPG)

Original file is available [here](https://drive.google.com/file/d/1e7OjuN_CmYkqcpvR32Ym-Uf5EoWfHyan/view?usp=sharing).
