from fastapi import APIRouter, FastAPI

from pyctuator.pyctuator_data import EnvironmentData, EndpointsData, InfoData, HealthData
from pyctuator.pyctuator_impl import PyctuatorImpl
from pyctuator.pyctuator_router import PyctuatorRouter
from pyctuator.metrics.metrics_provider import Metric, MetricNames


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
            return pyctuator_impl.get_endpoints()

        @router.options(path_prefix + "/env", include_in_schema=False)
        @router.options(path_prefix + "/info", include_in_schema=False)
        @router.options(path_prefix + "/health", include_in_schema=False)
        @router.options(path_prefix + "/metrics", include_in_schema=False)
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
        def get_health() -> HealthData:
            return pyctuator_impl.get_health()

        @router.get(path_prefix + "/metrics", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_metric_names() -> MetricNames:
            return pyctuator_impl.get_metric_names()

        @router.get(path_prefix + "/metrics/{metric_name}", tags=["pyctuator"])
        # pylint: disable=unused-variable
        def get_metric_measurement(metric_name: str) -> Metric:
            return pyctuator_impl.get_metric_measurement(metric_name)

        app.include_router(router)
