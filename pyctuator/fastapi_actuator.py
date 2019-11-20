from fastapi import APIRouter, FastAPI

from pyctuator.actuator_data import EnvironmentData, EndpointsData, InfoData, HealthData
from pyctuator.actuator_impl import Actuator
from pyctuator.actuator_router import ActuatorRouter
from pyctuator.metrics.metrics_provider import Metric, MetricNames


class FastApiActuator(ActuatorRouter):
    """
    An Actuator Class of type FastAPI, which holds the ActuatorRouter, and creates FastAPI routs
    """

    def __init__(
            self,
            app: FastAPI,
            actuator: Actuator
    ):
        super().__init__(app, actuator)
        router = APIRouter()

        @router.get("/actuator", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_endpoints() -> EndpointsData:
            return actuator.get_endpoints()

        @router.options("/actuator/env", include_in_schema=False)
        @router.options("/actuator/info", include_in_schema=False)
        @router.options("/actuator/health", include_in_schema=False)
        @router.options("/actuator/metrics", include_in_schema=False)
        # pylint: disable=unused-variable
        def options() -> None:
            """
            Spring boot admin, after registration, issues multiple OPTIONS request to the monitored application in order
            to determine the supported capabilities (endpoints).
            Here we "acknowledge" that env, info and health are supported.
            The "include_in_schema=False" is used to prevent from these OPTIONS endpoints to show up in the
            documentation.
            """

        @router.get("/actuator/env", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_environment() -> EnvironmentData:
            return actuator.get_environment()

        @router.get("/actuator/info", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_info() -> InfoData:
            return actuator.get_info()

        @router.get("/actuator/health", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_health() -> HealthData:
            return actuator.get_health()

        @router.get("/actuator/metrics", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_metric_names() -> MetricNames:
            return actuator.get_metric_names()

        @router.get("/actuator/metrics/{metric_name}", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_metric_measurement(metric_name: str) -> Metric:
            return actuator.get_metric_measurement(metric_name)

        app.include_router(router)
