import dataclasses
from datetime import datetime
from typing import Dict, Optional

from flask import Blueprint

from pyctuator.actuator_impl import Actuator


def get_blueprint(
        app_name: str,
        app_description: Optional[str],
        app_url: str,
        actuator_base_url: str,
        start_time: datetime) -> Blueprint:
    flask_blueprint: Blueprint = Blueprint('flask_blueprint', 'actuator', )
    actuator = Actuator(app_name, app_description, app_url, actuator_base_url, start_time)

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

    return flask_blueprint
