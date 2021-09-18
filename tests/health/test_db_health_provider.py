# pylint: disable=import-outside-toplevel
import importlib.util
import os

import pytest


@pytest.fixture
def require_sql_alchemy() -> None:
    if not importlib.util.find_spec("sqlalchemy"):
        pytest.skip("sqlalchemy is missing, skipping")


@pytest.fixture
def require_pymysql() -> None:
    if not importlib.util.find_spec("pymysql"):
        pytest.skip("PyMySQL is missing, skipping")


@pytest.fixture
def require_mysql_server() -> None:
    should_test_with_mysql = os.getenv("TEST_MYSQL_SERVER", None)
    if not should_test_with_mysql:
        pytest.skip("No MySQL server (env TEST_MYSQL_SERVER isn't True), skipping")


@pytest.mark.usefixtures("require_sql_alchemy")
def test_sqlite_health() -> None:
    from sqlalchemy import create_engine
    from pyctuator.health.db_health_provider import DbHealthProvider, DbHealthDetails, DbHealthStatus
    from pyctuator.health.health_provider import Status

    engine = create_engine("sqlite:///:memory:", echo=True)
    health_provider = DbHealthProvider(engine)
    assert health_provider.get_health() == DbHealthStatus(status=Status.UP, details=DbHealthDetails("sqlite"))


@pytest.mark.usefixtures("require_sql_alchemy", "require_pymysql", "require_mysql_server")
def test_mysql_health() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine
    from pyctuator.health.db_health_provider import DbHealthProvider, DbHealthDetails, DbHealthStatus
    from pyctuator.health.health_provider import Status

    engine: Engine = create_engine("mysql+pymysql://root:root@localhost:3306", echo=True)
    health_provider = DbHealthProvider(engine)
    assert health_provider.get_health() == DbHealthStatus(status=Status.UP, details=DbHealthDetails("mysql"))

    engine = create_engine("mysql+pymysql://kukipuki:blahblah@localhost:3306", echo=True)
    health_provider = DbHealthProvider(engine)
    health = health_provider.get_health()
    assert health.status == Status.DOWN
    details: DbHealthDetails = health.details
    assert details.failure is not None
    assert "Access denied for user" in details.failure
