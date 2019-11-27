# pylint: disable=import-outside-toplevel
import importlib.util
from typing import List

from pyctuator.metrics.metrics_provider import MetricsProvider, Metric, Measurement

PREFIX = "memory."


class MemoryMetricsProvider(MetricsProvider):
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
        if not self.process:
            return []
        keys: List[str] = list(self.process.memory_info()._asdict().keys())
        return list(map(lambda metric: PREFIX + metric, list(keys)))

    def get_metric(self, metric_name: str) -> Metric:
        measurements: List[Measurement] = []
        if self.process:
            name = metric_name[len(PREFIX):]
            measurements = [Measurement("VALUE", getattr(self.process.memory_info(), name))]
        return Metric(metric_name, None, "bytes", measurements, [])
