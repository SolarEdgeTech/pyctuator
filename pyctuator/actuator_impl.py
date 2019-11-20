from datetime import datetime
import os
from typing import Optional
from typing import List

from pyctuator.actuator_data import EndpointsData, EnvironmentData, InfoData, PropertyValue, PropertySource, \
    LinkHref, EndpointsLinks, AppInfo, BuildInfo, HealthData
from pyctuator.metrics.memory_metrics_impl import MemoryMetricsProvider
from pyctuator.metrics.metrics_provider import Metric, MetricNames
from pyctuator.metrics.thread_metrics_impl import ThreadMetricsProvider


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
        self.metric_providers = [
            MemoryMetricsProvider(),
            ThreadMetricsProvider(),
        ]

    def get_endpoints(self) -> EndpointsData:
        return EndpointsData(EndpointsLinks(
            LinkHref(self.actuator_base_url, False),
            LinkHref(self.actuator_base_url + "/env", False),
            LinkHref(self.actuator_base_url + "/info", False),
            LinkHref(self.actuator_base_url + "/health", False),
            LinkHref(self.actuator_base_url + "/metrics", False),
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

    def get_metric_names(self) -> MetricNames:
        metric_names = []
        for provider in self.metric_providers:
            for metric_name in provider.get_supported_metric_names():
                metric_names.append(metric_name)
        return MetricNames(metric_names)

    def get_metric_measurement(self, metric_name: str) -> Metric:
        for provider in self.metric_providers:
            if metric_name.startswith(provider.get_prefix()):
                return provider.get_metric(metric_name)
        raise KeyError(f"Unknown metric {metric_name}")
