import importlib.util
from typing import List, Optional

import psutil

from pyctuator.metrics.metrics_provider import MetricsProvider, Metric, Measurement

PREFIX = "thread."
THREAD_COUNT = PREFIX + "count"


class ThreadMetricsProvider(MetricsProvider):
    process: Optional[psutil.Process]

    def __init__(self) -> None:
        if importlib.util.find_spec("psutil"):
            self.process = psutil.Process()
        else:
            self.process = None

    def get_prefix(self) -> str:
        return PREFIX

    def get_supported_metric_names(self) -> List[str]:
        return [THREAD_COUNT]

    def get_metric(self, metric_name: str) -> Metric:
        measurements: List[Measurement] = []
        if self.process:
            measurements = [Measurement("COUNT", self.process.num_threads())]
        return Metric(metric_name, None, "Integer", measurements, [])
