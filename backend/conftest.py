import os
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

# Prefer the private local test connection when available. Set it before loading
# app settings so all imports use the isolated test database from the outset.
test_env_file = Path(__file__).with_name(".env.test")
if test_env_file.is_file():
    for line in test_env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = line.partition("=")[2].strip().strip("\"'")
            break

# Read the configured credentials, then force the dedicated test database name.
from app.core.config import settings

TEST_DATABASE_NAME = "aura_test_db"
test_database_url = make_url(settings.DATABASE_URL).set(database=TEST_DATABASE_NAME)
settings.DATABASE_URL = test_database_url.render_as_string(hide_password=False)
os.environ["DATABASE_URL"] = settings.DATABASE_URL

from app.database.base import Base
from app.database.connection import engine, get_db
from app.main import app


def _assert_test_database(url):
    assert url.database == TEST_DATABASE_NAME, (
        "Tests may only connect to aura_test_db; refusing database "
        f"{url.database!r}."
    )


_assert_test_database(engine.url)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Recheck immediately before any schema operation. Both destructive calls
    # are therefore refused unless the engine targets the exact test DB name.
    _assert_test_database(engine.url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    _assert_test_database(engine.url)
    Base.metadata.drop_all(bind=engine)
