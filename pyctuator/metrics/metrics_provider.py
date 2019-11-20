from abc import ABC, abstractmethod
from dataclasses import dataclass

from typing import List, Optional


@dataclass
class MetricNames:
    names: List[str]


@dataclass
class Measurement:
    statistic: str  # one of TOTAL, TOTAL_TIME, COUNT, MAX, VALUE, UNKNOWN, ACTIVE_TASKS, DURATION
    value: float  # can be an int as well


@dataclass
class MetricTag:
    tag: str
    values: List[str]


@dataclass
class Metric:
    name: str
    description: Optional[str]
    baseUnit: str
    measurements: List[Measurement]
    availableTags: List[MetricTag]


class MetricsProvider(ABC):

    @abstractmethod
    def get_prefix(self) -> str:
        pass

    @abstractmethod
    def get_supported_metric_names(self) -> List[str]:
        pass

    @abstractmethod
    def get_metric(self, metric_name: str) -> Metric:
        pass
