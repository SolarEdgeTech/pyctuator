from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, FastAPI

from pyctuator.actuator_data import EnvironmentData, EndpointsData, InfoData, HealthData
from pyctuator.actuator_router import ActuatorRouter
from pyctuator.actuator_impl import Actuator


class FastApiActuator(ActuatorRouter):

    def __init__(
            self,
            app: FastAPI,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            actuator_base_url: str,
            start_time: datetime
    ):
        super().__init__(app, app_name, app_description, app_url, actuator_base_url, start_time)
        router = APIRouter()
        actuator = Actuator(actuator_base_url)

        @router.get("/actuator", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_endpoints() -> EndpointsData:
            return actuator.get_endpoints()

        @router.options("/actuator/env", include_in_schema=False)
        @router.options("/actuator/info", include_in_schema=False)
        @router.options("/actuator/health", include_in_schema=False)
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

        app.include_router(router)
