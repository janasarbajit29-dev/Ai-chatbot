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
from app.core.config import settings

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
        email="quality1@test.com",
        name="user1",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(user1)
    db_session.commit()
    
    yield
    
    db_session.query(DocumentChunk).delete()
    db_session.query(Document).delete()
    db_session.query(User).delete()
    db_session.commit()

def get_auth_token(email: str, password: str = "password"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

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
            # Deterministic mock based on text to test threshold
            # High similarity if text contains 'highly relevant'
            if 'highly relevant' in contents.lower():
                emb = [1.0] * 3072
            else:
                emb = [-1.0] * 3072 # Orthogonal/opposite, will fail threshold
            
            # Normalize to avoid pgvector errors if necessary, but pgvector handles it
            return MockResponse(emb)

    class MockClient:
        models = MockModels()

    def mock_get_genai_client():
        return MockClient()

    monkeypatch.setattr("app.services.embedding_service.get_genai_client", mock_get_genai_client)

def test_retrieval_threshold_and_quality(db_session, mock_genai_client):
    user = db_session.query(User).filter_by(email="quality1@test.com").first()
    
    # Manually create documents and chunks
    doc1 = Document(
        user_id=user.id,
        original_filename="resume.pdf",
        stored_filename="resume_1.pdf",
        file_type="pdf",
        mime_type="application/pdf",
        file_size=1024,
        storage_path="/dev/null",
        processing_status="ready"
    )
    db_session.add(doc1)
    db_session.commit()
    
    # Highly relevant chunk (simulated by having 'highly relevant')
    chunk1 = DocumentChunk(
        document_id=doc1.id,
        user_id=user.id,
        chunk_index=0,
        content="This is highly relevant text about React and Python.",
        embedding=[1.0] * 3072
    )
    # Another relevant chunk in the same document
    chunk2 = DocumentChunk(
        document_id=doc1.id,
        user_id=user.id,
        chunk_index=1,
        content="Another highly relevant text.",
        embedding=[1.0] * 3072
    )
    # A fourth one (should be filtered out by 3-chunks-per-doc deduplication)
    chunk3 = DocumentChunk(
        document_id=doc1.id,
        user_id=user.id,
        chunk_index=2,
        content="highly relevant chunk 3.",
        embedding=[1.0] * 3072
    )
    chunk4 = DocumentChunk(
        document_id=doc1.id,
        user_id=user.id,
        chunk_index=3,
        content="highly relevant chunk 4.",
        embedding=[1.0] * 3072
    )
    
    # Weak chunk
    chunk_weak = DocumentChunk(
        document_id=doc1.id,
        user_id=user.id,
        chunk_index=4,
        content="Random college activities.",
        embedding=[-1.0] * 3072 # Will have low similarity
    )
    
    db_session.add_all([chunk1, chunk2, chunk3, chunk4, chunk_weak])
    db_session.commit()
    
    # Test retrieval
    from app.services.rag_retrieval_service import retrieve_relevant_chunks
    # "highly relevant query" will get embedding [1.0] * 3072
    results = retrieve_relevant_chunks(db_session, user.id, "highly relevant query", top_k=5)
    
    # Should only return max 3 from doc1, and the weak one should be filtered entirely!
    assert len(results) == 3
    # Check that the weak chunk is not present
    for r in results:
        assert r.chunk_index in [0, 1, 2] # The first 3 relevant ones

def test_no_results_fallback(db_session, mock_genai_client, monkeypatch):
    user = db_session.query(User).filter_by(email="quality1@test.com").first()
    token = get_auth_token("quality1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Query without "highly relevant" will get [-1.0]*3072, so it won't match the relevant chunks
    
    # Mock AI response
    def mock_generate_response(messages):
        # If fallback, it will just receive the normal prompt
        return "Normal chat response"
        
    monkeypatch.setattr("app.services.ai_service.ai_service.generate_response", mock_generate_response)
    
    # Main chat endpoint requires conversation_id
    res_conv = client.post("/api/conversations/", json={"title": "Test"}, headers=headers)
    conv_id = res_conv.json()["id"]
    
    res = client.post("/api/chat/", json={"conversation_id": conv_id, "content": "random query"}, headers=headers)
    assert res.status_code == 200
    
    data = res.json()
    assert data["assistant_message"]["content"] == "Normal chat response"
    assert data["sources"] == [] # No fake citations
