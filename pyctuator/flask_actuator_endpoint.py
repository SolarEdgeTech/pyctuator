from typing import Dict

from flask import Blueprint

from pyctuator.actuator_impl import Actuator


def get_blueprint(actuator_base_url: str) -> Blueprint:
    flask_blueprint: Blueprint = Blueprint('flask_blueprint', 'actuator', )
    actuator = Actuator(actuator_base_url)

    @flask_blueprint.route("/actuator")
    # pylint: disable=unused-variable
    def get_endpoints() -> Dict:
        return actuator.get_endpoints()

    @flask_blueprint.route("/actuator/env")
    # pylint: disable=unused-variable
    def get_environment() -> Dict:
        return actuator.get_environment()

    @flask_blueprint.route("/actuator/info")
    # pylint: disable=unused-variable
    def get_info() -> Dict:
        return actuator.get_info()

    @flask_blueprint.route("/actuator/health")
    # pylint: disable=unused-variable
    def get_health() -> Dict:
        return actuator.get_health()

    return flask_blueprint
