# pylint: disable=import-outside-toplevel

import importlib.util
import os

import pytest


@pytest.fixture
def require_redis() -> None:
    if not importlib.util.find_spec("redis"):
        pytest.skip("redis is missing, skipping")


@pytest.mark.usefixtures("require_redis")
@pytest.fixture
def require_redis_server() -> None:
    should_test_with_redis = os.getenv("TEST_REDIS_SERVER", None)
    if not should_test_with_redis:
        pytest.skip("No Redis server (env TEST_REDIS_SERVER isn't True), skipping")


@pytest.mark.usefixtures("require_redis", "require_redis_server")
def test_redis_health() -> None:
    import redis
    from pyctuator.health.health_provider import Status
    from pyctuator.health.redis_health_provider import RedisHealthProvider, RedisHealthStatus, RedisHealthDetails

    health = RedisHealthProvider(redis.Redis()).get_health()
    assert health == RedisHealthStatus(Status.UP, RedisHealthDetails("5.0.3", "standalone"))


@pytest.mark.usefixtures("require_redis", "require_redis_server")
def test_redis_bad_password() -> None:
    import redis
    from pyctuator.health.health_provider import Status
    from pyctuator.health.redis_health_provider import RedisHealthProvider

    health = RedisHealthProvider(redis.Redis(password="blabla")).get_health()
    assert health.status == Status.DOWN
    assert "Client sent AUTH, but no password is set" in str(health.details.failure)
