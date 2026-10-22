
# Tests for the auth endpoints, named after the cases in the Testing Plan (TC-01 to TC-06).

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy import select

from app.config import settings
from app.database.session import SessionLocal
from app.models.user import User


# TC-01: successful registration, password stored hashed
def test_register_creates_user_with_hashed_password(client):
    response = client.post("/auth/register", json={"email": "New@Example.com", "password": "longenough1"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body and "password_hash" not in body

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "new@example.com"))
        assert user is not None
        assert user.password_hash != "longenough1"
        assert user.password_hash.startswith("$2")


# TC-02: duplicate email rejected
def test_register_duplicate_email_rejected(client, registered_user):
    response = client.post("/auth/register", json=registered_user)
    assert response.status_code == 409


def test_register_duplicate_email_is_case_insensitive(client, registered_user):
    response = client.post(
        "/auth/register",
        json={"email": registered_user["email"].upper(), "password": "another-password"},
    )
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post("/auth/register", json={"email": "a@b.co", "password": "short"})
    assert response.status_code == 422


def test_register_rejects_invalid_email(client):
    response = client.post("/auth/register", json={"email": "not-an-email", "password": "longenough1"})
    assert response.status_code == 422


# TC-03: successful login returns a usable JWT
def test_login_returns_token(client, registered_user):
    response = client.post("/auth/login", json=registered_user)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


# TC-04: wrong password rejected, no token issued
def test_login_wrong_password_rejected(client, registered_user):
    response = client.post("/auth/login", json={"email": registered_user["email"], "password": "wrong-password"})
    assert response.status_code == 401
    assert "access_token" not in response.json()


def test_login_unknown_email_rejected_with_same_message(client, registered_user):
    wrong_pw = client.post("/auth/login", json={"email": registered_user["email"], "password": "wrong-password"})
    unknown = client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert unknown.status_code == 401
    assert unknown.json()["detail"] == wrong_pw.json()["detail"]


# TC-05: protected route blocks a missing token
def test_me_without_token_rejected(client):
    assert client.get("/auth/me").status_code == 401


# TC-06: protected route blocks malformed, wrongly signed and expired tokens
def test_me_with_malformed_token_rejected(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_with_wrong_signature_rejected(client, registered_user):
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "some-other-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_me_with_expired_token_rejected(client, registered_user):
    token = client.post("/auth/login", json=registered_user).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    expired = jwt.encode(
        {"sub": me["id"], "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_me_with_valid_token_returns_user(client, registered_user):
    token = client.post("/auth/login", json=registered_user).json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == registered_user["email"]


def test_token_for_deleted_user_rejected(client, registered_user):
    token = client.post("/auth/login", json=registered_user).json()["access_token"]
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == registered_user["email"]))
        db.delete(user)
        db.commit()
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
