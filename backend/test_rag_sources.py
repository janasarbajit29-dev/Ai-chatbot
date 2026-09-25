import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.core.security import get_password_hash
import uuid

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
    db_session.query(Message).delete()
    db_session.query(Conversation).delete()
    db_session.query(User).delete()
    db_session.commit()
    
    from datetime import date
    user1 = User(
        email="source1@test.com",
        name="sourceuser1",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    user2 = User(
        email="source2@test.com",
        name="sourceuser2",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    
    yield
    
    db_session.query(DocumentChunk).delete()
    db_session.query(Document).delete()
    db_session.query(Message).delete()
    db_session.query(Conversation).delete()
    db_session.query(User).delete()
    db_session.commit()

def get_auth_token(email: str, password: str = "password"):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )
    return response.json()["access_token"]

def create_mock_doc_and_chunks(db: Session, user_id: int, filename: str, chunks_data: list):
    doc = Document(
        user_id=user_id,
        original_filename=filename,
        stored_filename=f"{uuid.uuid4().hex}_{filename}",
        file_type="pdf",
        mime_type="application/pdf",
        file_size=100,
        storage_path=f"/tmp/test_{filename}",
        processing_status="ready"
    )
    db.add(doc)
    db.commit()
    
    for i, (content, embedding) in enumerate(chunks_data):
        chunk = DocumentChunk(
            document_id=doc.id, 
            user_id=user_id, 
            chunk_index=i, 
            content=content, 
            embedding=embedding
        )
        db.add(chunk)
    db.commit()
    return doc

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
            # All queries match our specific test chunks for simplicity
            emb[0] = 1.0 
            return MockResponse(emb)

    class MockClient:
        models = MockModels()

    def mock_get_genai_client():
        return MockClient()

    monkeypatch.setattr("app.services.embedding_service.get_genai_client", mock_get_genai_client)

@pytest.fixture
def mock_ai_service(monkeypatch):
    def mock_generate_response(messages):
        last_message = messages[-1].content
        if "SYSTEM INSTRUCTIONS" in last_message and "BEGIN DOCUMENT CONTEXT" in last_message:
            return "RAG Grounded Answer"
        return "Normal AI Answer"
    
    def mock_generate_stream_response(messages):
        resp = mock_generate_response(messages)
        yield resp

    monkeypatch.setattr("app.services.ai_service.ai_service.generate_response", mock_generate_response)
    monkeypatch.setattr("app.services.ai_service.ai_service.generate_stream_response", mock_generate_stream_response)


def test_normal_chat_no_fake_sources(db_session, mock_genai_client, mock_ai_service):
    token = get_auth_token("source1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Test1"}, headers=headers)
    conv_id = res.json()["id"]
    
    response = client.post(
        "/api/chat/",
        json={"conversation_id": conv_id, "content": "What is AI?"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"]["content"] == "Normal AI Answer"
    assert data["sources"] == []

def test_rag_chat_with_sources(db_session, mock_genai_client, mock_ai_service):
    user = db_session.query(User).filter_by(email="source1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    create_mock_doc_and_chunks(db_session, user.id, "resume.pdf", [("I know React", emb)])
    
    token = get_auth_token("source1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Test2"}, headers=headers)
    conv_id = res.json()["id"]
    
    response = client.post(
        "/api/chat/",
        json={"conversation_id": conv_id, "content": "What do I know?"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"]["content"] == "RAG Grounded Answer"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["filename"] == "resume.pdf"
    assert "document_id" in data["sources"][0]
    assert "relevance" in data["sources"][0]

def test_source_deduplication(db_session, mock_genai_client, mock_ai_service):
    user = db_session.query(User).filter_by(email="source1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    create_mock_doc_and_chunks(db_session, user.id, "dedup.pdf", [("chunk1", emb), ("chunk2", emb)])
    
    token = get_auth_token("source1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Test3"}, headers=headers)
    conv_id = res.json()["id"]
    
    response = client.post(
        "/api/chat/",
        json={"conversation_id": conv_id, "content": "Find dedup chunks"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"]["content"] == "RAG Grounded Answer"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["filename"] == "dedup.pdf"

def test_multiple_documents(db_session, mock_genai_client, mock_ai_service):
    user = db_session.query(User).filter_by(email="source1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    create_mock_doc_and_chunks(db_session, user.id, "doc1.pdf", [("chunk1", emb)])
    create_mock_doc_and_chunks(db_session, user.id, "doc2.pdf", [("chunk2", emb)])
    
    token = get_auth_token("source1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Test4"}, headers=headers)
    conv_id = res.json()["id"]
    
    response = client.post(
        "/api/chat/",
        json={"conversation_id": conv_id, "content": "Find from both"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    
    filenames = sorted([s["filename"] for s in data["sources"]])
    assert "doc1.pdf" in filenames
    assert "doc2.pdf" in filenames

def test_cross_user_source_protection(db_session, mock_genai_client, mock_ai_service):
    # User 2 uploads a document
    user2 = db_session.query(User).filter_by(email="source2@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    create_mock_doc_and_chunks(db_session, user2.id, "top_secret.pdf", [("secret", emb)])
    
    # User 1 queries
    token = get_auth_token("source1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Test5"}, headers=headers)
    conv_id = res.json()["id"]
    
    response = client.post(
        "/api/chat/",
        json={"conversation_id": conv_id, "content": "What is the secret?"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    # User 1 should get normal AI answer with NO sources
    assert data["assistant_message"]["content"] == "Normal AI Answer"
    assert len(data["sources"]) == 0

def test_streaming_sse_source_event(db_session, mock_genai_client, mock_ai_service):
    user = db_session.query(User).filter_by(email="source1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    create_mock_doc_and_chunks(db_session, user.id, "stream.pdf", [("stream chunk", emb)])
    
    token = get_auth_token("source1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Test6"}, headers=headers)
    conv_id = res.json()["id"]
    
    response = client.post(
        "/api/chat/stream",
        json={"conversation_id": conv_id, "content": "Streaming query"},
        headers=headers
    )
    assert response.status_code == 200
    
    stream_output = response.text
    # Should have 'chunk' events
    assert "type\": \"chunk\"" in stream_output
    assert "RAG Grounded Answer" in stream_output
    # Should have a 'sources' event with the filename
    assert "type\": \"sources\"" in stream_output
    assert "stream.pdf" in stream_output
