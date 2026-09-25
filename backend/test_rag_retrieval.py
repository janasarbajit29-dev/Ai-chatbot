import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.core.security import get_password_hash
from app.services.embedding_service import get_genai_client

# Dummy test setup
client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(autouse=True)
def setup_teardown(db_session):
    # Setup
    db_session.query(DocumentChunk).delete()
    db_session.query(Document).delete()
    db_session.query(User).delete()
    db_session.commit()
    
    from datetime import date
    user1 = User(
        email="rag1@test.com",
        name="raguser1",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    user2 = User(
        email="rag2@test.com",
        name="raguser2",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    
    yield
    
    # Teardown
    db_session.query(DocumentChunk).delete()
    db_session.query(Document).delete()
    db_session.query(User).delete()
    db_session.commit()

def get_auth_token(email: str, password: str = "password"):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        raise ValueError(f"Login failed: {response.text}")
    return response.json()["access_token"]

import uuid

def create_mock_chunk(db: Session, user_id: int, content: str, embedding: list[float], chunk_index: int = 0):
    unique_name = f"test_{uuid.uuid4().hex}.txt"
    doc = Document(
        user_id=user_id,
        original_filename=unique_name,
        stored_filename=unique_name,
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        storage_path=f"/tmp/{unique_name}",
        processing_status="ready"
    )
    db.add(doc)
    db.commit()
    chunk = DocumentChunk(document_id=doc.id, user_id=user_id, chunk_index=chunk_index, content=content, embedding=embedding)
    db.add(chunk)
    db.commit()

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
            if not contents or not contents.strip():
                raise ValueError("Contents cannot be empty")
            # Generate a fake 3072-dimensional embedding
            # For testing, we make the first dimension 1.0, rest 0.0
            emb = [0.0] * 3072
            emb[0] = 1.0
            return MockResponse(emb)

    class MockClient:
        models = MockModels()

    def mock_get_genai_client():
        return MockClient()

    monkeypatch.setattr("app.services.embedding_service.get_genai_client", mock_get_genai_client)


def test_empty_query_rejected(db_session, mock_genai_client):
    token = get_auth_token("rag1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/rag/retrieve",
        json={"query": "", "top_k": 5},
        headers=headers
    )
    assert response.status_code == 400
    assert "Query cannot be empty" in response.json()["detail"]

def test_invalid_top_k_rejected(db_session, mock_genai_client):
    token = get_auth_token("rag1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Negative top_k
    response = client.post(
        "/api/rag/retrieve",
        json={"query": "test query", "top_k": -1},
        headers=headers
    )
    assert response.status_code == 422 # Pydantic validation error

    # Huge top_k
    response = client.post(
        "/api/rag/retrieve",
        json={"query": "test query", "top_k": 100},
        headers=headers
    )
    assert response.status_code == 422 # Pydantic validation error

def test_no_matching_chunks(db_session, mock_genai_client):
    token = get_auth_token("rag1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/rag/retrieve",
        json={"query": "test query", "top_k": 5},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["results"] == []

def test_authenticated_user_retrieval_and_cross_user_protection(db_session, mock_genai_client):
    user1 = db_session.query(User).filter_by(email="rag1@test.com").first()
    user2 = db_session.query(User).filter_by(email="rag2@test.com").first()
    
    # Create chunks for User 1
    emb1 = [0.0] * 3072
    emb1[0] = 0.9 # Closer to the mock query (1.0, 0, ...)
    create_mock_chunk(db_session, user1.id, "User 1 Chunk 1", emb1)
    
    emb2 = [0.0] * 3072
    emb2[0] = 0.5 # Less close
    create_mock_chunk(db_session, user1.id, "User 1 Chunk 2", emb2)
    
    # Create chunks for User 2 (very close, but belongs to user 2)
    emb3 = [0.0] * 3072
    emb3[0] = 0.99 
    create_mock_chunk(db_session, user2.id, "User 2 Chunk 1", emb3)
    
    token = get_auth_token("rag1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Search
    response = client.post(
        "/api/rag/retrieve",
        json={"query": "test query", "top_k": 5},
        headers=headers
    )
    
    assert response.status_code == 200
    results = response.json()["results"]
    
    # User 1 should only see their 2 chunks
    assert len(results) == 2
    
    # Order should be by similarity: Chunk 1 then Chunk 2
    assert results[0]["content"] == "User 1 Chunk 1"
    assert results[1]["content"] == "User 1 Chunk 2"
    
    # Ensure User 2's chunk is NOT in the results
    for r in results:
        assert r["content"] != "User 2 Chunk 1"
        assert r["similarity"] > 0

def test_top_k_works(db_session, mock_genai_client):
    user1 = db_session.query(User).filter_by(email="rag1@test.com").first()
    
    for i in range(10):
        emb = [0.0] * 3072
        emb[0] = 0.1 * i
        create_mock_chunk(db_session, user1.id, f"Chunk {i}", emb, chunk_index=i)
        
    token = get_auth_token("rag1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/rag/retrieve",
        json={"query": "test query", "top_k": 3},
        headers=headers
    )
    
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 3
