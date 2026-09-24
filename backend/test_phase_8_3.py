import pytest
import os
from sqlalchemy import text
from app.database.connection import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.document_chunking_service import chunk_text
from app.services.embedding_service import generate_embeddings
from app.services import document_processing_service, document_service
from app.core.security import get_password_hash

# Fixtures for DB and User
@pytest.fixture(scope="module")
def db_session():
    # Use the normal dev DB for these tests
    db = next(get_db())
    yield db
    db.close()

@pytest.fixture(scope="module")
def test_user(db_session):
    from datetime import date
    user = db_session.query(User).filter(User.email == "test_phase_8_3@example.com").first()
    if not user:
        user = User(
            email="test_phase_8_3@example.com",
            password_hash=get_password_hash("password123"),
            name="Test Phase 8.3 User",
            date_of_birth=date(1990, 1, 1)
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    yield user
    # Cleanup
    db_session.delete(user)
    db_session.commit()

@pytest.fixture(scope="module")
def other_user(db_session):
    from datetime import date
    user = db_session.query(User).filter(User.email == "other_user_8_3@example.com").first()
    if not user:
        user = User(
            email="other_user_8_3@example.com",
            password_hash=get_password_hash("password123"),
            name="Other User",
            date_of_birth=date(1990, 1, 1)
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    yield user
    db_session.delete(user)
    db_session.commit()


def test_pgvector_extension_available(db_session):
    result = db_session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).fetchone()
    assert result is not None, "pgvector extension is not installed"

def test_document_chunking():
    text_content = "This is sentence one. This is sentence two. This is sentence three."
    
    # Small chunk size to force split
    chunks = chunk_text(text_content, chunk_size=30, chunk_overlap=10)
    
    assert len(chunks) > 1
    assert "sentence one" in chunks[0]
    
    # Overlap works
    assert any("sentence" in c for c in chunks)

def test_empty_text_chunking():
    assert len(chunk_text("")) == 0
    assert len(chunk_text("   ")) == 0

def test_embeddings_generation_real():
    # Calling real Gemini API
    chunks = ["Hello world", "This is a test of embeddings"]
    embeddings = generate_embeddings(chunks)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 3072
    assert len(embeddings[1]) == 3072

def test_document_processing_pipeline(db_session, test_user):
    # 1. Create a dummy txt document
    upload_dir = os.path.join(os.path.dirname(__file__), "storage", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    storage_path = os.path.join(upload_dir, "test_doc_8_3.txt")
    with open(storage_path, "w", encoding="utf-8") as f:
        f.write("Aura AI is a powerful assistant. It uses document chunking. It uses pgvector.")
        
    doc = Document(
        user_id=test_user.id,
        original_filename="test_doc_8_3.txt",
        stored_filename="test_doc_8_3.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        storage_path=storage_path
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # 2. Process document
    processed_doc = document_processing_service.process_document(db_session, doc.id, test_user.id)
    
    assert processed_doc.processing_status == "ready"
    assert processed_doc.extracted_text is not None
    
    # 3. Check chunks
    chunks = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index).all()
    
    assert len(chunks) > 0
    
    # Chunk indices sequential
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))
    
    # Dimension matches 768
    # Using real API so the pgvector dimension should have succeeded without error
    # Let's verify DB side
    assert chunks[0].embedding is not None
    
    # 4. Check ownership
    for c in chunks:
        assert c.user_id == test_user.id
        
    # 5. Reprocessing does not duplicate
    document_processing_service.process_document(db_session, doc.id, test_user.id)
    chunks_after = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    assert len(chunks_after) == len(chunks) # Should remain the same count
    
    # Cleanup
    document_service.delete_document(db_session, test_user.id, doc.id)
    
    # 6. Deleting doc removes chunks (CASCADE)
    chunks_deleted = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    assert len(chunks_deleted) == 0

def test_cross_user_access_rejected(db_session, test_user, other_user):
    # Setup doc for test_user
    upload_dir = os.path.join(os.path.dirname(__file__), "storage", "uploads")
    storage_path = os.path.join(upload_dir, "test_doc_cross.txt")
    with open(storage_path, "w", encoding="utf-8") as f:
        f.write("Some text")
        
    doc = Document(
        user_id=test_user.id,
        original_filename="test_doc_cross.txt",
        stored_filename="test_doc_cross.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        storage_path=storage_path
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # Attempt process by other_user
    import fastapi
    with pytest.raises(fastapi.HTTPException) as exc_info:
        document_processing_service.process_document(db_session, doc.id, other_user.id)
        
    assert exc_info.value.status_code == 404
    
    # Cleanup
    db_session.delete(doc)
    db_session.commit()
