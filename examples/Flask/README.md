# Flask example
This example demonstrates the integration with the [Flask](https://flask.palletsprojects.com/) web-framework.

## Running the example
1. Start an instance of SBA (Spring Boot Admin):
    ```sh
    docker run --rm -p 8080:8080 michayaak/spring-boot-admin:2.2.3-1
    ```
2. Once Spring Boot Admin is running, you can run the examples as follow:
    ```sh
    cd examples/Flask
    poetry install
    poetry run python -m flask_example_app
    ``` 

![Flask Example](../images/Flask.png)

## Notes
* Note that when Flask debugging is enabled, Pyctuator and Flask are initialized twice because Flask reloads the script. This causes Pyctuator to register twice thus the `startup` time alternates between the time these instances started.
    ```Python
    app.run(port=5000, host="0.0.0.0", debug=True)
    ```
