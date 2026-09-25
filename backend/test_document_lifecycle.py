import pytest
import os
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.core.security import get_password_hash

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(autouse=True)
def setup_teardown(db_session):
    db_session.query(DocumentChunk).delete()
    db_session.query(Document).delete()
    db_session.query(User).delete()
    db_session.commit()
    
    from datetime import date
    user1 = User(
        email="lifecycle1@test.com",
        name="user1",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    user2 = User(
        email="lifecycle2@test.com",
        name="user2",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    
    yield
    
    db_session.query(DocumentChunk).delete()
    db_session.query(Document).delete()
    db_session.query(User).delete()
    db_session.commit()

def get_auth_token(email: str, password: str = "password"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

import tempfile

def create_dummy_txt_file(content: str):
    path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

@pytest.fixture
def mock_genai_client(monkeypatch):
    class MockResponse:
        class Embedding:
            def __init__(self, values):
                self.values = values
        def __init__(self, values):
            self.embeddings = [self.Embedding(values)]

    class MockModels:
        def embed_content(self, model, contents, config):
            emb = [0.0] * 3072
            emb[0] = 1.0 
            return MockResponse(emb)

    class MockClient:
        models = MockModels()

    def mock_get_genai_client():
        return MockClient()

    monkeypatch.setattr("app.services.embedding_service.get_genai_client", mock_get_genai_client)

def test_document_lifecycle(db_session, mock_genai_client):
    token = get_auth_token("lifecycle1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Upload Document
    file_path = create_dummy_txt_file("This is a test document with enough text to be chunked.")
    
    with open(file_path, "rb") as f:
        res = client.post("/api/files/upload", files={"file": ("test1.txt", f, "text/plain")}, headers=headers)
        
    assert res.status_code == 201
    doc_id = res.json()["id"]
    
    # Check duplicate upload prevention
    with open(file_path, "rb") as f:
        res_dup = client.post("/api/files/upload", files={"file": ("test1.txt", f, "text/plain")}, headers=headers)
    assert res_dup.status_code == 409
    
    # 2. Process Document
    res = client.post(f"/api/files/{doc_id}/process", headers=headers)
    assert res.status_code == 200
    assert res.json()["processing_status"] == "ready"
    
    # Check chunks and embeddings
    chunks = db_session.query(DocumentChunk).filter_by(document_id=doc_id).all()
    assert len(chunks) > 0
    assert chunks[0].embedding is not None
    
    # 3. Reprocessing does not duplicate
    res = client.post(f"/api/files/{doc_id}/process", headers=headers)
    assert res.status_code == 200
    chunks_after = db_session.query(DocumentChunk).filter_by(document_id=doc_id).all()
    assert len(chunks) == len(chunks_after)
    
    # 4. Delete removes everything
    res = client.delete(f"/api/files/{doc_id}", headers=headers)
    assert res.status_code == 204
    
    doc = db_session.query(Document).filter_by(id=doc_id).first()
    assert doc is None
    chunks_deleted = db_session.query(DocumentChunk).filter_by(document_id=doc_id).all()
    assert len(chunks_deleted) == 0

def test_empty_document_handling(db_session, mock_genai_client):
    token = get_auth_token("lifecycle1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    file_path = create_dummy_txt_file("   \n\n  ")
    
    with open(file_path, "rb") as f:
        res = client.post("/api/files/upload", files={"file": ("empty.txt", f, "text/plain")}, headers=headers)
        
    doc_id = res.json()["id"]
    
    res = client.post(f"/api/files/{doc_id}/process", headers=headers)
    assert res.status_code == 400
    
    doc = db_session.query(Document).filter_by(id=doc_id).first()
    assert doc.processing_status == "failed"
    
    chunks = db_session.query(DocumentChunk).filter_by(document_id=doc_id).all()
    assert len(chunks) == 0

def test_processing_failure_rollback(db_session, monkeypatch):
    token = get_auth_token("lifecycle1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    file_path = create_dummy_txt_file("Valid text")
    with open(file_path, "rb") as f:
        res = client.post("/api/files/upload", files={"file": ("fail.txt", f, "text/plain")}, headers=headers)
    doc_id = res.json()["id"]
    
    def mock_extract(*args, **kwargs):
        raise Exception("Fatal error")
        
    monkeypatch.setattr("app.services.document_processing_service.extract_text_from_txt", mock_extract)
    
    res = client.post(f"/api/files/{doc_id}/process", headers=headers)
    assert res.status_code == 500
    
    doc = db_session.query(Document).filter_by(id=doc_id).first()
    assert doc.processing_status == "failed"
    assert doc.processing_error == "An unexpected error occurred during processing."

def test_cross_user_protection(db_session):
    token1 = get_auth_token("lifecycle1@test.com")
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    token2 = get_auth_token("lifecycle2@test.com")
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    file_path = create_dummy_txt_file("Secret for user 1")
    with open(file_path, "rb") as f:
        res = client.post("/api/files/upload", files={"file": ("secret.txt", f, "text/plain")}, headers=headers1)
    doc_id = res.json()["id"]
    
    # User 2 tries to process
    res = client.post(f"/api/files/{doc_id}/process", headers=headers2)
    assert res.status_code == 404
    
    # User 2 tries to delete
    res = client.delete(f"/api/files/{doc_id}", headers=headers2)
    assert res.status_code == 404
