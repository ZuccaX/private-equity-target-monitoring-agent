from collections.abc import Iterator
from pathlib import Path

from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import assert_safe_test_database_url, settings
from app.core.database import get_db
from main import create_app


API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def test_database_url() -> str:
    database_url = settings.test_database_url
    assert_safe_test_database_url(database_url)
    return database_url


@pytest.fixture(scope="session")
def alembic_config(test_database_url: str) -> Config:
    config = Config(API_ROOT / "alembic.ini")
    config.attributes["database_url"] = test_database_url
    return config


@pytest.fixture(scope="session")
def test_engine(test_database_url: str) -> Iterator[Engine]:
    engine = create_engine(test_database_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def reset_test_schema(test_engine: Engine) -> Iterator[None]:
    with test_engine.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    # pgvector's PostgreSQL type OID changes when the schema/extension is
    # recreated. Reusing a psycopg connection would retain the old adapter OID.
    test_engine.dispose()
    yield


@pytest.fixture
def migrated_test_schema(
    alembic_config: Config,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "head")


@pytest.fixture
def db_session(
    test_engine: Engine,
    migrated_test_schema: None,
) -> Iterator[Session]:
    session_factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def api_client(db_session: Session) -> Iterator[TestClient]:
    application = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as client:
        yield client
    application.dependency_overrides.clear()
