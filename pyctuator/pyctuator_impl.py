import os
from datetime import datetime
from typing import List
from typing import Optional
from urllib.parse import urlparse

from pyctuator.health.diskspace_health_impl import DiskSpaceHealthProvider
from pyctuator.metrics.memory_metrics_impl import MemoryMetricsProvider
from pyctuator.metrics.metrics_provider import Metric, MetricNames
from pyctuator.metrics.thread_metrics_impl import ThreadMetricsProvider
from pyctuator.pyctuator_data import (
    EnvironmentData,
    InfoData,
    PropertyValue,
    PropertySource,
    AppInfo,
    BuildInfo,
    HealthData
)


class PyctuatorImpl:

    # pylint: disable=too-many-instance-attributes

    def __init__(
            self,
            app_name: str,
            app_description: Optional[str],
            pyctuator_endpoint_url: str,
            start_time: datetime,
            free_disk_space_down_threshold_bytes: int,
    ):
        self.app_name = app_name
        self.app_description = app_description
        self.start_time = start_time
        self.pyctuator_endpoint_url = pyctuator_endpoint_url
        self.metric_providers = [
            MemoryMetricsProvider(),
            ThreadMetricsProvider(),
        ]
        self.health_providers = [
            DiskSpaceHealthProvider(free_disk_space_down_threshold_bytes)
        ]

        # Determine the endpoint's URL path prefix and make sure it doesn't ends with a "/"
        self.pyctuator_endpoint_path_prefix = urlparse(pyctuator_endpoint_url).path
        if self.pyctuator_endpoint_path_prefix[-1:] == "/":
            self.pyctuator_endpoint_path_prefix = self.pyctuator_endpoint_path_prefix[:-1]

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
        service_is_up = True
        details = {}
        for provider in self.health_providers:
            if provider.is_supported():
                health = provider.get_health()
                service_is_up = service_is_up and health.status == "UP"
                details[provider.get_name()] = health

        return HealthData(
            "UP" if service_is_up else "DOWN",
            details)

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
