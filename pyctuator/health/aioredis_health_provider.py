import asyncio

from pyctuator.health.health_provider import Status
from pyctuator.health.redis_health_provider import RedisHealthStatus, RedisHealthDetails, RedisHealthProvider


class AioRedisHealthProvider(RedisHealthProvider):
    def get_health(self) -> RedisHealthStatus:
        try:
            info = asyncio.run(self.redis.info())

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
