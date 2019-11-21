from typing import Optional, Dict

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from pyctuator.environment.environment_provider import EnvironmentData
from pyctuator.health.health_provider import HealthSummary
from pyctuator.logging.pyctuator_logging import LoggersData, LoggerLevels
from pyctuator.metrics.metrics_provider import Metric, MetricNames
from pyctuator.pyctuator_impl import PyctuatorImpl, InfoData
from pyctuator.pyctuator_router import PyctuatorRouter, EndpointsData


class FastApiLoggerItem(BaseModel):
    configuredLevel: Optional[str]


class FastApiPyctuator(PyctuatorRouter):

    def __init__(
            self,
            app: FastAPI,
            pyctuator_impl: PyctuatorImpl,
    ):
        super().__init__(app, pyctuator_impl)
        path_prefix = pyctuator_impl.pyctuator_endpoint_path_prefix
        router = APIRouter()

        @router.get(path_prefix, tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_endpoints() -> EndpointsData:
            return self.get_endpoints_data()

        @router.options(path_prefix + "/env", include_in_schema=False)
        @router.options(path_prefix + "/info", include_in_schema=False)
        @router.options(path_prefix + "/health", include_in_schema=False)
        @router.options(path_prefix + "/metrics", include_in_schema=False)
        @router.options(path_prefix + "/loggers", include_in_schema=False)
        # pylint: disable=unused-variable
        def options() -> None:
            """
            Spring boot admin, after registration, issues multiple OPTIONS request to the monitored application in order
            to determine the supported capabilities (endpoints).
            Here we "acknowledge" that env, info and health are supported.
            The "include_in_schema=False" is used to prevent from these OPTIONS endpoints to show up in the
            documentation.
            """

        @router.get(path_prefix + "/env", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_environment() -> EnvironmentData:
            return pyctuator_impl.get_environment()

        @router.get(path_prefix + "/info", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_info() -> InfoData:
            return pyctuator_impl.get_info()

        @router.get(path_prefix + "/health", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_health() -> HealthSummary:
            return pyctuator_impl.get_health()

        @router.get(path_prefix + "/metrics", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_metric_names() -> MetricNames:
            return pyctuator_impl.get_metric_names()

        @router.get(path_prefix + "/metrics/{metric_name}", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_metric_measurement(metric_name: str) -> Metric:
            return pyctuator_impl.get_metric_measurement(metric_name)

        # Retrieving All Loggers
        @router.get(path_prefix + "/loggers", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_loggers() -> LoggersData:
            return pyctuator_impl.logging.get_loggers()

        @router.post(path_prefix + "/loggers/{logger_name}", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def set_logger_level(item: FastApiLoggerItem, logger_name: str) -> Dict:
            pyctuator_impl.logging.set_logger_level(logger_name, item.configuredLevel)
            return {}

        @router.get(path_prefix + "/loggers/{logger_name}", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_logger(logger_name: str) -> LoggerLevels:
            return pyctuator_impl.logging.get_logger(logger_name)

        app.include_router(router)
