# FastAPI example
This example demonstrates the integration with the [FastAPI](https://fastapi.tiangolo.com/) web-framework.

## Running the example
1. Start an instance of SBA (Spring Boot Admin):
    ```sh
    docker run --rm -p 8080:8080 michayaak/spring-boot-admin:2.2.3-1
    ```
2. Once Spring Boot Admin is running, you can run the examples as follow:
    ```sh
    cd examples/FastAPI
    poetry install
    poetry run python -m fastapi_example_app
    ``` 

![FastAPI Example](../images/FastAPI.png)