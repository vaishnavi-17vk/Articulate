
# Test setup: a throwaway database that is rebuilt for every test, plus shared fixtures.

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_articulate.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only"

import pytest
from fastapi.testclient import TestClient

from app.database.session import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    creds = {"email": "speaker@example.com", "password": "correct-horse-battery"}
    response = client.post("/auth/register", json=creds)
    assert response.status_code == 201
    return creds
