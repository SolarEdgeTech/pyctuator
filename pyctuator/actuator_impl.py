from datetime import datetime
import os
import sys
from typing import Optional
from typing import List

from pyctuator.actuator_data import EndpointsData, EnvironmentData, InfoData, PropertyValue, PropertySource, \
    LinkHref, EndpointsLinks, AppInfo, BuildInfo, HealthData


class Actuator:
    """
    A Logic Class that holds the app data which is used in implementation, and implementation logic
    """

    def __init__(
            self,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            actuator_base_url: str,
            start_time: datetime
    ):
        self.app_name = app_name
        self.app_description = app_description
        self.app_url = app_url
        self.actuator_base_url = actuator_base_url
        self.start_time = start_time

    def get_endpoints(self) -> EndpointsData:
        return EndpointsData(EndpointsLinks(
            LinkHref(self.actuator_base_url),
            LinkHref(self.actuator_base_url + "/env"),
            LinkHref(self.actuator_base_url + "/info"),
            LinkHref(self.actuator_base_url + "/health"),
        ))

    def get_environment(self) -> EnvironmentData:
        properties_dict = {key: PropertyValue(value) for (key, value) in os.environ.items()}
        property_src = [(PropertySource("systemEnvironment", properties_dict))]
        active_profiles: List[str] = list()
        env_data = EnvironmentData(active_profiles, property_src)
        return env_data

    def get_info(self) -> InfoData:
        return InfoData(AppInfo(self.app_name, self.app_description),
                        BuildInfo("version", "artifact", self.app_name, "group", self.start_time))

    def get_health(self) -> HealthData:
        details_dict = {"status": "UP", "details": "More details"}
        return HealthData("UP", details_dict)
