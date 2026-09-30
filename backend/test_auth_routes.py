from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_rejects_unknown_user():
    response = client.post(
        "/api/auth/login",
        json={"email": "pytest-unknown@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_signup_and_login_use_test_database():
    user = {
        "name": "Pytest User",
        "email": "pytest-recovery@example.com",
        "password": "pytest-password",
        "confirm_password": "pytest-password",
        "date_of_birth": "1990-01-01",
    }

    signup = client.post("/api/auth/signup", json=user)
    assert signup.status_code == 201
    assert signup.json()["email"] == user["email"]

    duplicate_signup = client.post("/api/auth/signup", json=user)
    assert duplicate_signup.status_code == 409

    login = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["user"]["email"] == user["email"]
