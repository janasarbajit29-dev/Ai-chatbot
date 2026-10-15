import pytest
import uuid
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
from app.services.rag_retrieval_service import retrieve_relevant_chunks

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
        email="docuser1@test.com",
        name="docuser1",
        password_hash=get_password_hash("password"),
        date_of_birth=date(1990, 1, 1)
    )
    user2 = User(
        email="docuser2@test.com",
        name="docuser2",
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

def create_test_doc_with_chunks(db: Session, user_id: int, filename: str, text: str, chunks_data: list):
    doc = Document(
        user_id=user_id,
        original_filename=filename,
        stored_filename=f"{uuid.uuid4().hex}_{filename}",
        file_type="pdf",
        mime_type="application/pdf",
        file_size=2048,
        storage_path=f"/tmp/{filename}",
        processing_status="ready",
        extracted_text=text
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
            if not contents or not contents.strip():
                raise ValueError("Contents cannot be empty")
            emb = [0.0] * 3072
            if "Python" in contents:
                emb[1] = 1.0
            else:
                emb[0] = 1.0
            return MockResponse(emb)

    class MockClient:
        models = MockModels()

    monkeypatch.setattr("app.services.embedding_service.get_genai_client", lambda: MockClient())

@pytest.fixture
def mock_ai_service(monkeypatch):
    def mock_generate_response(messages):
        last_message = messages[-1].content
        if "BEGIN DOCUMENT CONTEXT" in last_message:
            return "Grounded analysis of attached document."
        return "Normal AI response."
    
    def mock_generate_stream_response(messages):
        yield mock_generate_response(messages)

    monkeypatch.setattr("app.services.ai_service.ai_service.generate_response", mock_generate_response)
    monkeypatch.setattr("app.services.ai_service.ai_service.generate_stream_response", mock_generate_stream_response)

def test_get_document_by_id_and_extracted_text(db_session):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    user2 = db_session.query(User).filter_by(email="docuser2@test.com").first()
    
    emb = [0.0] * 3072
    emb[0] = 1.0
    doc1 = create_test_doc_with_chunks(
        db_session, user1.id, "handbook.pdf", "Chapter 1: Intro to Handbook\nChapter 2: Policies", [("Chapter 1", emb)]
    )
    
    token1 = get_auth_token("docuser1@test.com")
    token2 = get_auth_token("docuser2@test.com")
    
    # User 1 retrieves their document
    res = client.get(f"/api/files/{doc1.id}", headers={"Authorization": f"Bearer {token1}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == doc1.id
    assert data["original_filename"] == "handbook.pdf"
    assert data["extracted_text"] == "Chapter 1: Intro to Handbook\nChapter 2: Policies"
    assert data["processing_status"] == "ready"
    
    # User 2 tries to retrieve User 1's document (privacy check)
    res_unauth = client.get(f"/api/files/{doc1.id}", headers={"Authorization": f"Bearer {token2}"})
    assert res_unauth.status_code == 404

def test_document_prioritization_and_isolation(db_session, mock_genai_client):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    
    emb = [0.0] * 3072
    emb[0] = 1.0
    
    doc_target = create_test_doc_with_chunks(
        db_session, user1.id, "target.pdf", "Target content", [("Target chunk content", emb)]
    )
    doc_other = create_test_doc_with_chunks(
        db_session, user1.id, "other.pdf", "Other content", [("Other chunk content", emb)]
    )
    
    # 1. When target_doc.id is specified, only target_doc chunks should be retrieved
    chunks = retrieve_relevant_chunks(db_session, user1.id, "Target query", top_k=5, document_id=doc_target.id)
    assert len(chunks) == 1
    assert chunks[0].document_id == doc_target.id
    assert "Target chunk" in chunks[0].content
    
    # 2. Other document is NOT in the retrieved chunks
    doc_ids = {c.document_id for c in chunks}
    assert doc_other.id not in doc_ids

def test_cross_user_attached_document_protection(db_session, mock_genai_client):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    user2 = db_session.query(User).filter_by(email="docuser2@test.com").first()
    
    emb = [0.0] * 3072
    emb[0] = 1.0
    doc2 = create_test_doc_with_chunks(
        db_session, user2.id, "private.pdf", "Private text", [("Private chunk", emb)]
    )
    
    # User 1 tries to attach User 2's document_id
    chunks = retrieve_relevant_chunks(db_session, user1.id, "What is inside?", top_k=5, document_id=doc2.id)
    assert len(chunks) == 0

def test_chat_stream_with_attached_document(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    doc = create_test_doc_with_chunks(
        db_session, user1.id, "report.pdf", "Report text", [("Annual Report 2026 data", emb)]
    )
    
    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create conversation
    res = client.post("/api/conversations/", json={"title": "Doc Chat"}, headers=headers)
    conv_id = res.json()["id"]
    
    # Send message with document_id
    res_chat = client.post(
        "/api/chat/stream",
        json={
            "conversation_id": conv_id,
            "content": "Summarize this PDF.",
            "document_id": doc.id
        },
        headers=headers
    )
    assert res_chat.status_code == 200
    stream_text = res_chat.text
    assert "Grounded analysis of attached document." in stream_text
    assert "sources" in stream_text
    assert "report.pdf" in stream_text


def test_new_chat_without_pdf_answers_python_using_normal_ai(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    create_test_doc_with_chunks(
        db_session, user1.id, "existing_guide.pdf", "Existing text", [("Existing chunk", emb)]
    )
    
    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Start a new chat without attaching any PDF
    res = client.post("/api/conversations/", json={"title": "Normal Chat"}, headers=headers)
    conv_id = res.json()["id"]
    
    res_chat = client.post(
        "/api/chat/stream",
        json={
            "conversation_id": conv_id,
            "content": "What is Python?",
            "document_id": None
        },
        headers=headers
    )
    assert res_chat.status_code == 200
    stream_text = res_chat.text
    # Normal AI response, no RAG context, no sources
    assert "Normal AI response." in stream_text
    assert "Grounded analysis" not in stream_text
    assert "sources" not in stream_text
    assert "existing_guide.pdf" not in stream_text


def test_uploading_pdf_and_requesting_summary_produces_answer_based_on_pdf(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    doc = create_test_doc_with_chunks(
        db_session, user1.id, "architecture_overview.pdf", "Architecture Overview details", [("Microservices architecture overview", emb)]
    )
    
    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Summary Chat"}, headers=headers)
    conv_id = res.json()["id"]
    
    # Request a summary with the attached PDF
    res_chat = client.post(
        "/api/chat/stream",
        json={
            "conversation_id": conv_id,
            "content": "Summarize this PDF",
            "document_id": doc.id
        },
        headers=headers
    )
    assert res_chat.status_code == 200
    stream_text = res_chat.text
    assert "Grounded analysis of attached document." in stream_text
    assert "sources" in stream_text
    assert "architecture_overview.pdf" in stream_text


def test_pdf_attached_to_one_conversation_never_used_in_another_conversation(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    doc = create_test_doc_with_chunks(
        db_session, user1.id, "confidential.pdf", "Confidential text", [("Confidential data", emb)]
    )
    
    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Conversation 1: PDF is attached
    res1 = client.post("/api/conversations/", json={"title": "Conv 1 with PDF"}, headers=headers)
    conv1_id = res1.json()["id"]
    
    res_chat1 = client.post(
        "/api/chat/stream",
        json={
            "conversation_id": conv1_id,
            "content": "Explain this document",
            "document_id": doc.id
        },
        headers=headers
    )
    assert res_chat1.status_code == 200
    assert "Grounded analysis of attached document." in res_chat1.text
    assert "confidential.pdf" in res_chat1.text
    
    # Conversation 2: New chat, no PDF attached
    res2 = client.post("/api/conversations/", json={"title": "Conv 2 Normal"}, headers=headers)
    conv2_id = res2.json()["id"]
    
    res_chat2 = client.post(
        "/api/chat/stream",
        json={
            "conversation_id": conv2_id,
            "content": "What is Python?",
            "document_id": None
        },
        headers=headers
    )
    assert res_chat2.status_code == 200
    stream_text2 = res_chat2.text
    # Conversation 2 MUST NOT use confidential.pdf from Conversation 1!
    assert "Normal AI response." in stream_text2
    assert "confidential.pdf" not in stream_text2
    assert "sources" not in stream_text2


def test_new_chat_asking_what_is_java_uses_normal_ai_generation_sync(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0  # Perfect vector match for general queries if retrieval were erroneously run
    create_test_doc_with_chunks(
        db_session, user1.id, "my_resume.pdf", "Java skill listed on page 1", [("Java skill", emb)]
    )

    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    # New conversation with no PDF attached
    res_conv = client.post("/api/conversations/", json={"title": "Java Question Chat"}, headers=headers)
    conv_id = res_conv.json()["id"]

    # Synchronous chat request without document_id
    response = client.post(
        "/api/chat/",
        json={
            "conversation_id": conv_id,
            "content": "what is Java?",
            "document_id": None
        },
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    # Must use normal AI generation and not retrieve the resume
    assert data["assistant_message"]["content"] == "Normal AI response."
    assert data["sources"] == []


def test_new_chat_asking_what_is_java_uses_normal_ai_generation_stream(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    create_test_doc_with_chunks(
        db_session, user1.id, "my_resume.pdf", "Java skill listed on page 1", [("Java skill", emb)]
    )

    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    res_conv = client.post("/api/conversations/", json={"title": "Java Stream Chat"}, headers=headers)
    conv_id = res_conv.json()["id"]

    # Streaming chat request without document_id
    response = client.post(
        "/api/chat/stream",
        json={
            "conversation_id": conv_id,
            "content": "what is Java?",
            "document_id": None
        },
        headers=headers
    )
    assert response.status_code == 200
    stream_output = response.text
    assert "Normal AI response." in stream_output
    assert "Grounded analysis" not in stream_output
    assert "my_resume.pdf" not in stream_output
    assert '"type": "sources"' not in stream_output


def test_explicitly_attached_pdf_is_used_for_its_conversation_sync(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    doc = create_test_doc_with_chunks(
        db_session, user1.id, "java_deep_dive.pdf", "Java Virtual Machine details", [("JVM architecture", emb)]
    )

    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    res_conv = client.post("/api/conversations/", json={"title": "Attached PDF Chat"}, headers=headers)
    conv_id = res_conv.json()["id"]

    # Explicitly attached document_id passed
    response = client.post(
        "/api/chat/",
        json={
            "conversation_id": conv_id,
            "content": "Explain this document",
            "document_id": doc.id
        },
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_message"]["content"] == "Grounded analysis of attached document."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_id"] == doc.id
    assert data["sources"][0]["filename"] == "java_deep_dive.pdf"


def test_pdf_from_one_conversation_never_leaks_into_another_both_sync_and_stream(db_session, mock_genai_client, mock_ai_service):
    user1 = db_session.query(User).filter_by(email="docuser1@test.com").first()
    emb = [0.0] * 3072
    emb[0] = 1.0
    doc = create_test_doc_with_chunks(
        db_session, user1.id, "project_spec.pdf", "Project specification text", [("Specification details", emb)]
    )

    token = get_auth_token("docuser1@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Conversation 1: with attached PDF
    conv1 = client.post("/api/conversations/", json={"title": "Conv 1"}, headers=headers).json()
    res_sync1 = client.post(
        "/api/chat/",
        json={"conversation_id": conv1["id"], "content": "Summarize this PDF", "document_id": doc.id},
        headers=headers
    )
    assert res_sync1.status_code == 200
    assert res_sync1.json()["assistant_message"]["content"] == "Grounded analysis of attached document."

    # Conversation 2: unattached new conversation asking general question
    conv2 = client.post("/api/conversations/", json={"title": "Conv 2"}, headers=headers).json()
    
    # Check sync path in Conv 2
    res_sync2 = client.post(
        "/api/chat/",
        json={"conversation_id": conv2["id"], "content": "what is Java?", "document_id": None},
        headers=headers
    )
    assert res_sync2.status_code == 200
    assert res_sync2.json()["assistant_message"]["content"] == "Normal AI response."
    assert res_sync2.json()["sources"] == []

    # Check stream path in Conv 2
    res_stream2 = client.post(
        "/api/chat/stream",
        json={"conversation_id": conv2["id"], "content": "what is Java?", "document_id": None},
        headers=headers
    )
    assert res_stream2.status_code == 200
    assert "Normal AI response." in res_stream2.text
    assert "project_spec.pdf" not in res_stream2.text
    assert '"type": "sources"' not in res_stream2.text

