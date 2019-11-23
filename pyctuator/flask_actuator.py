from flask import Flask

from pyctuator.actuator_impl import Actuator
from pyctuator.actuator_router import ActuatorRouter
from pyctuator.flask_actuator_endpoint import get_blueprint


class FlaskActuator(ActuatorRouter):
    """
    An Actuator Class of type Flask, which holds the ActuatorRouter, and creates Flask routs
    """

    def __init__(
            self,
            app: Flask,
            actuator: Actuator
    ):
        super().__init__(app, actuator)
        app.register_blueprint(get_blueprint(
            actuator.app_name,
            actuator.app_description,
            actuator.app_url,
            actuator.actuator_base_url,
            actuator.start_time,
        ))
