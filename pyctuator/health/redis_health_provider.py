import importlib.util
from dataclasses import dataclass
from typing import Optional

from redis import Redis

from pyctuator.health.health_provider import HealthProvider, HealthStatus, Status, HealthDetails


@dataclass
class RedisHealthDetails(HealthDetails):
    version: Optional[str] = None
    mode: Optional[str] = None
    failure: Optional[str] = None


@dataclass
class RedisHealthStatus(HealthStatus):
    status: Status
    details: RedisHealthDetails


class RedisHealthProvider(HealthProvider):

    def __init__(self, redis: Redis) -> None:
        super().__init__()
        self.redis = redis

    def is_supported(self) -> bool:
        return importlib.util.find_spec("redis") is not None

    def get_name(self) -> str:
        return "redis"

    def get_health(self) -> RedisHealthStatus:
        try:
            info = self.redis.info()

            return RedisHealthStatus(
                status=Status.UP,
                details=RedisHealthDetails(
                    version=info["redis_version"],
                    mode=info["redis_mode"],
                ))
        except Exception as e:  # pylint: disable=broad-except
            return RedisHealthStatus(
                status=Status.DOWN,
                details=RedisHealthDetails(
                    failure=str(e)
                ))
