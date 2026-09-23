import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_unauthenticated_upload():
    response = client.post("/api/files/upload", files={"file": ("test.txt", b"hello world", "text/plain")})
    assert response.status_code == 401

def test_unauthenticated_list():
    response = client.get("/api/files/")
    assert response.status_code == 401
