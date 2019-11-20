import datetime
import os
import sys
from typing import Dict, List

from pyctuator.actuator_data import EndpointsData, EnvironmentData, InfoData, PropertyValue, PropertySource, \
    LinkHref, EndpointsLinks, AppInfo, BuildInfo, HealthData


class Actuator:
    def __init__(self, actuator_base_url: str) -> None:
        self.actuator_base_url = actuator_base_url

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
        return InfoData(AppInfo(sys.argv[0], sys.argv[0]),
                        BuildInfo("name1", sys.argv[0], sys.argv[0], "group1", str(datetime.datetime.now())))

    def get_health(self) -> HealthData:
        details_dict = {"status": "UP", "details": "More details"}
        return HealthData("UP", details_dict)
