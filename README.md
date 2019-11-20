# Pyctuator

Pyctuator is a Python implementation of the Spring Actuator API for popular web frameworks.  
Pyctuator implements a growing subset of the actuator API (see https://docs.spring.io/spring-boot/docs/2.1.8.RELEASE/actuator-api/html/) that allows monitoring Python applications using Spring Boot Admin.

## Why?

## Quickstart

## Configuration

## Examples
### Flask
```python
from flask import Flask

from pyctuator import pyctuator

myFlaskApp = Flask("ExampleFlaskApp")


@myFlaskApp.route("/")
def hello():
    return "Hello World!"


actuator_server_url = "http://127.0.0.1:5000"
pyctuator.init(
    myFlaskApp,
    "Flask Actuator",
    "Flask Actuator",
    actuator_server_url,
    f"{actuator_server_url}/actuator",
    "http://localhost:8080/instances",
    1
)

myFlaskApp.run(debug=True, port=5000, host="0.0.0.0")

```
### FastAPI
```python
from fastapi import FastAPI
from uvicorn.config import Config

from pyctuator import pyctuator
from uvicorn.config import Config


app = FastAPI(
    title="FastAPI Example Server",
    description="Demonstrate Spring Boot Admin Integration with FastAPI",
    docs_url="/api",
)


@app.get("/")
def read_root():
    return "Hello World!"


actuator_server_url = "http://127.0.0.1:8000"  # Local Application URL
pyctuator.init(
    app,
    "FastAPI Actuator",
    "FastAPI Actuator",
    actuator_server_url,
    f"{actuator_server_url}/actuator",
    "http://127.0.0.1:8080/instances",
    1
)

myFastAPIApp = Server(config=(Config(app=app, loop="asyncio", host="0.0.0.0")))
myFastAPIApp.run()

```


## Contributing
To set up a development environment, make sure you have Python 3.7 or newer installed, and execute `make bootstrap`.

Use `make check` to run static analysis tools.

Use `make test` to run tests.

### Design document
![Pyctuator](/uploads/8183be2327a2703be14a628d484b8a4b/Pyctuator.JPG)

Original file is available [here](https://drive.google.com/file/d/1e7OjuN_CmYkqcpvR32Ym-Uf5EoWfHyan/view?usp=sharing).
