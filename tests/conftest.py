import pytest
from fastapi.testclient import TestClient
from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
)
from sqlmodel.pool import StaticPool

from app.dependencies import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SQLModel.metadata.create_all(engine)


def override_get_db():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(name="client")
def client_fixture():
    with TestClient(app) as client:
        yield client
