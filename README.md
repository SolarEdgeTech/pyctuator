# Pyctuator

Pyctuator is a Python implementation of the Spring Actuator API for popular web frameworks which allows a web application written in Python to be managed and monitored by codecentric's [Spring Boot Admin](https://github.com/codecentric/spring-boot-admin).  
Pyctuator implements a growing subset of the actuator API (see https://docs.spring.io/spring-boot/docs/2.1.8.RELEASE/actuator-api/html/) that allows monitoring Python applications using Spring Boot Admin.

## Why?

## Quickstart

## Configuration

## Examples
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
    "Flask Pyctuator Example",
    "http://localhost:5000",
    "http://localhost:5000/puctuator",
    "http://localhost:8080/instances"
)

myFlaskApp.run(debug=True, port=5000)

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
    "FastAPI Pyctuator Example",
    "http://localhost:8000",
    "http://localhost:8000/pyctuator",
    "http://localhost:8080/instances"
)

myFastAPIServer = Server(config=(Config(app=app, loop="asyncio")))
myFastAPIServer.run()

```


## Usage notes
### Using psutil for process/filesystem metrics
In order for pyctuator to provide process/filesystem metrics, it is using the *optional* `psutil` library from https://github.com/giampaolo/psutil (if the library isn't available in a system using the pyctuator, pyctuator will not provide such metrics). 

## Contributing
To set up a development environment, make sure you have Python 3.7 or newer installed, and execute `make bootstrap`.

Use `make check` to run static analysis tools.

Use `make test` to run tests.

### Design document
![Pyctuator](/uploads/8183be2327a2703be14a628d484b8a4b/Pyctuator.JPG)

Original file is available [here](https://drive.google.com/file/d/1e7OjuN_CmYkqcpvR32Ym-Uf5EoWfHyan/view?usp=sharing).
