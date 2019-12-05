# pylint: disable=import-outside-toplevel
import importlib.util
from dataclasses import dataclass

from pyctuator.health.health_provider import HealthProvider, HealthDetails, HealthStatus, Status


@dataclass
class DiskSpaceHealthDetails(HealthDetails):
    total: int
    free: int
    threshold: int


@dataclass
class DiskSpaceHealth(HealthStatus):
    status: Status
    details: DiskSpaceHealthDetails


class DiskSpaceHealthProvider(HealthProvider):

    def __init__(self, free_bytes_down_threshold: int) -> None:
        self.free_bytes_down_threshold = free_bytes_down_threshold

        if importlib.util.find_spec("psutil"):
            # psutil is optional and must only be imported if it is installed
            import psutil
            self.psutil = psutil
        else:
            self.psutil = None

    def is_supported(self) -> bool:
        return self.psutil is not None

    def get_name(self) -> str:
        return "diskSpace"

    def get_health(self) -> DiskSpaceHealth:
        usage = self.psutil.disk_usage(".")
        return DiskSpaceHealth(
            Status.UP if usage.free > self.free_bytes_down_threshold else Status.DOWN,
            DiskSpaceHealthDetails(usage.total, usage.free, self.free_bytes_down_threshold)
        )
