from datetime import datetime
from typing import Optional

from flask import Flask

from pyctuator.actuator_router import ActuatorRouter
from pyctuator.flask_actuator_endpoint import get_blueprint


class FlaskActuator(ActuatorRouter):

    def __init__(
            self,
            app: Flask,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            actuator_base_url: str,
            start_time: datetime
    ):
        super().__init__(app, app_name, app_description, app_url, actuator_base_url, start_time)
        app.register_blueprint(get_blueprint(actuator_base_url))
