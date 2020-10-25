from dataclasses import dataclass
from datetime import datetime
from typing import List
from typing import Mapping
from typing import Optional
from urllib.parse import urlparse

from pyctuator.environment.environment_provider import EnvironmentData, EnvironmentProvider
from pyctuator.health.health_provider import HealthStatus, HealthSummary, Status, HealthProvider
from pyctuator.httptrace.http_tracer import HttpTracer
from pyctuator.logfile.logfile import PyctuatorLogfile  # type: ignore
from pyctuator.logging.pyctuator_logging import PyctuatorLogging
from pyctuator.metrics.metrics_provider import Metric, MetricNames, MetricsProvider
from pyctuator.threads.thread_dump_provider import ThreadDump, ThreadDumpProvider


@dataclass
class GitCommitInfo:
    time: datetime
    id: str


@dataclass
class GitInfo:
    commit: GitCommitInfo
    branch: Optional[str] = None


@dataclass
class BuildInfo:
    name: Optional[str] = None
    artifact: Optional[str] = None
    group: Optional[str] = None
    version: Optional[str] = None
    time: Optional[datetime] = None


@dataclass
class AppDetails:
    name: str
    description: Optional[str] = None


@dataclass
class AppInfo:
    app: AppDetails
    build: Optional[BuildInfo] = None
    git: Optional[GitInfo] = None


class PyctuatorImpl:
    # pylint: disable=too-many-instance-attributes
    def __init__(
            self,
            app_info: AppInfo,
            pyctuator_endpoint_url: str,
            logfile_max_size: int,
            logfile_formatter: str,
    ):
        self.app_info = app_info
        self.pyctuator_endpoint_url = pyctuator_endpoint_url

        self.metrics_providers: List[MetricsProvider] = []
        self.health_providers: List[HealthProvider] = []
        self.environment_providers: List[EnvironmentProvider] = []
        self.logging = PyctuatorLogging()
        self.thread_dump_provider = ThreadDumpProvider()
        self.logfile = PyctuatorLogfile(max_size=logfile_max_size, formatter=logfile_formatter)
        self.http_tracer = HttpTracer()

        # Determine the endpoint's URL path prefix and make sure it doesn't end with a "/"
        self.pyctuator_endpoint_path_prefix = urlparse(pyctuator_endpoint_url).path
        if self.pyctuator_endpoint_path_prefix[-1:] == "/":
            self.pyctuator_endpoint_path_prefix = self.pyctuator_endpoint_path_prefix[:-1]

    def register_metrics_provider(self, provider: MetricsProvider) -> None:
        self.metrics_providers.append(provider)

    def register_health_providers(self, provider: HealthProvider) -> None:
        self.health_providers.append(provider)

    def register_environment_provider(self, provider: EnvironmentProvider) -> None:
        self.environment_providers.append(provider)

    def get_environment(self) -> EnvironmentData:
        active_profiles: List[str] = list()
        env_data = EnvironmentData(
            active_profiles,
            [source.get_properties_source() for source in self.environment_providers]
        )
        return env_data

    def set_git_info(self, git_info: GitInfo) -> None:
        self.app_info.git = git_info

    def set_build_info(self, build_info: BuildInfo) -> None:
        self.app_info.build = build_info

    def get_health(self) -> HealthSummary:
        health_statuses: Mapping[str, HealthStatus] = {
            provider.get_name(): provider.get_health()
            for provider in self.health_providers
            if provider.is_supported()
        }

        # Health is UP if no provider is registered
        if not health_statuses:
            return HealthSummary(Status.UP, health_statuses)

        # If there's at least one provider and any of the providers is DOWN, the service is DOWN
        service_is_down = any(health_status.status == Status.DOWN for health_status in health_statuses.values())
        if service_is_down:
            return HealthSummary(Status.DOWN, health_statuses)

        # IF there's at least one provider and none of the providers is DOWN and at least one is UP, the service is UP
        service_is_up = any(health_status.status == Status.UP for health_status in health_statuses.values())
        if service_is_up:
            return HealthSummary(Status.UP, health_statuses)

        # else, all providers are unknown so the service is UNKNOWN
        return HealthSummary(Status.UNKNOWN, health_statuses)

    def get_metric_names(self) -> MetricNames:
        metric_names = []
        for provider in self.metrics_providers:
            for metric_name in provider.get_supported_metric_names():
                metric_names.append(metric_name)
        return MetricNames(metric_names)

    def get_metric_measurement(self, metric_name: str) -> Metric:
        for provider in self.metrics_providers:
            if metric_name.startswith(provider.get_prefix()):
                return provider.get_metric(metric_name)
        raise KeyError(f"Unknown metric {metric_name}")

    def get_thread_dump(self) -> ThreadDump:
        return self.thread_dump_provider.get_thread_dump()
