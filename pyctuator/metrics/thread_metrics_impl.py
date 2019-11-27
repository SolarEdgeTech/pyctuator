# pylint: disable=import-outside-toplevel
import importlib.util
from typing import List

from pyctuator.metrics.metrics_provider import MetricsProvider, Metric, Measurement

PREFIX = "thread."
THREAD_COUNT = PREFIX + "count"


class ThreadMetricsProvider(MetricsProvider):
    def __init__(self) -> None:
        if importlib.util.find_spec("psutil"):
            # psutil is optional and must only be imported if it is installed
            import psutil
            self.process = psutil.Process()
        else:
            self.process = None

    def get_prefix(self) -> str:
        return PREFIX

    def get_supported_metric_names(self) -> List[str]:
        return [THREAD_COUNT] if self.process else []

    def get_metric(self, metric_name: str) -> Metric:
        measurements = [Measurement("COUNT", self.process.num_threads())] if self.process else []
        return Metric(metric_name, None, "Integer", measurements, [])
