import dataclasses
from typing import Dict

from flask import Blueprint
from flask import Flask

from pyctuator.actuator_impl import Actuator
from pyctuator.actuator_router import ActuatorRouter


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

        flask_blueprint: Blueprint = Blueprint('flask_blueprint', 'actuator', )
        actuator = Actuator(
            actuator.app_name,
            actuator.app_description,
            actuator.app_url,
            actuator.actuator_base_url,
            actuator.start_time)

        @flask_blueprint.route("/actuator")
        # pylint: disable=unused-variable
        def get_endpoints() -> Dict:
            return dataclasses.asdict(actuator.get_endpoints())

        @flask_blueprint.route("/actuator/env")
        # pylint: disable=unused-variable
        def get_environment() -> Dict:
            return dataclasses.asdict(actuator.get_environment())

        @flask_blueprint.route("/actuator/info")
        # pylint: disable=unused-variable
        def get_info() -> Dict:
            return dataclasses.asdict(actuator.get_info())

        @flask_blueprint.route("/actuator/health")
        # pylint: disable=unused-variable
        def get_health() -> Dict:
            return dataclasses.asdict(actuator.get_health())

        @flask_blueprint.route("/actuator/metrics")
        # pylint: disable=unused-variable
        def get_metric_names() -> Dict:
            return dataclasses.asdict(actuator.get_metric_names())

        @flask_blueprint.route("/actuator/metrics/<metric_name>")
        # pylint: disable=unused-variable
        def get_metric_measurement(metric_name: str) -> Dict:
            return dataclasses.asdict(actuator.get_metric_measurement(metric_name))

        app.register_blueprint(flask_blueprint)
