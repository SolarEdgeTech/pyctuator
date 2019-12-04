import dataclasses
from typing import Dict

from flask import Blueprint
from flask import Flask

from pyctuator.pyctuator_impl import PyctuatorImpl
from pyctuator.pyctuator_router import PyctuatorRouter


class FlaskPyctuator(PyctuatorRouter):

    def __init__(
            self,
            app: Flask,
            pyctuator_impl: PyctuatorImpl
    ):
        super().__init__(app, pyctuator_impl)
        path_prefix = pyctuator_impl.pyctuator_endpoint_path_prefix
        flask_blueprint: Blueprint = Blueprint("flask_blueprint", "pyctuator", )

        @flask_blueprint.route(path_prefix)
        # pylint: disable=unused-variable
        def get_endpoints() -> Dict:
            return dataclasses.asdict(self.get_endpoints_data())

        @flask_blueprint.route(path_prefix + "/env")
        # pylint: disable=unused-variable
        def get_environment() -> Dict:
            return dataclasses.asdict(pyctuator_impl.get_environment())

        @flask_blueprint.route(path_prefix + "/info")
        # pylint: disable=unused-variable
        def get_info() -> Dict:
            return dataclasses.asdict(pyctuator_impl.get_info())

        @flask_blueprint.route(path_prefix + "/health")
        # pylint: disable=unused-variable
        def get_health() -> Dict:
            return dataclasses.asdict(pyctuator_impl.get_health())

        @flask_blueprint.route(path_prefix + "/metrics")
        # pylint: disable=unused-variable
        def get_metric_names() -> Dict:
            return dataclasses.asdict(pyctuator_impl.get_metric_names())

        @flask_blueprint.route(path_prefix + "/metrics/<metric_name>")
        # pylint: disable=unused-variable
        def get_metric_measurement(metric_name: str) -> Dict:
            return dataclasses.asdict(pyctuator_impl.get_metric_measurement(metric_name))

        app.register_blueprint(flask_blueprint)
