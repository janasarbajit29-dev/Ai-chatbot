import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database.connection import get_db
from app.models.user import User
from app.models.document import Document
from app.services.document_processing_service import clean_text
import uuid

# Reusable auth headers and client
client = TestClient(app)

def override_get_db():
    from app.database.connection import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def db():
    from app.database.connection import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def setup_users(db: Session):
    # Setup test users
    user1 = db.query(User).filter(User.email == "test_8_2_u1@example.com").first()
    if not user1:
        from datetime import date
        user1 = User(email="test_8_2_u1@example.com", name="Test U1", password_hash="hash", date_of_birth=date(1990, 1, 1))
        db.add(user1)
    
    user2 = db.query(User).filter(User.email == "test_8_2_u2@example.com").first()
    if not user2:
        from datetime import date
        user2 = User(email="test_8_2_u2@example.com", name="Test U2", password_hash="hash", date_of_birth=date(1990, 1, 1))
        db.add(user2)
        
    db.commit()
    db.refresh(user1)
    db.refresh(user2)
    
    return user1, user2

@pytest.fixture
def auth_headers_u1(setup_users):
    u1, _ = setup_users
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": str(u1.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_u2(setup_users):
    _, u2 = setup_users
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": str(u2.id)})
    return {"Authorization": f"Bearer {token}"}

def create_mock_txt_file(content: str = "Test Content", filename: str = "test.txt"):
    upload_dir = os.path.join(os.path.dirname(__file__), "storage", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4()}_{filename}"
    path = os.path.join(upload_dir, stored_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return stored_name, path

def test_clean_text():
    raw = "Hello   world.\n\n\n\nThis is a \r\n test.  \n"
    cleaned = clean_text(raw)
    assert cleaned == "Hello world.\n\nThis is a \n test."

def test_process_txt_success(db: Session, setup_users, auth_headers_u1):
    u1, _ = setup_users
    stored_name, path = create_mock_txt_file("Bengali: নমস্কার. English: Hello.")
    
    doc = Document(
        user_id=u1.id,
        original_filename="test.txt",
        stored_filename=stored_name,
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        storage_path=path,
        processing_status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    response = client.post(f"/api/files/{doc.id}/process", headers=auth_headers_u1)
    assert response.status_code == 200
    data = response.json()
    assert data["processing_status"] == "ready"
    assert data["processing_error"] is None
    
    # Verify in DB
    db.expire_all()
    db_doc = db.query(Document).filter(Document.id == doc.id).first()
    assert "নমস্কার" in db_doc.extracted_text
    assert "Hello" in db_doc.extracted_text

def test_process_cross_user_protection(db: Session, setup_users, auth_headers_u1, auth_headers_u2):
    u1, u2 = setup_users
    stored_name, path = create_mock_txt_file()
    
    # Owned by U1
    doc = Document(
        user_id=u1.id,
        original_filename="secret.txt",
        stored_filename=stored_name,
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        storage_path=path
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # U2 tries to process
    response = client.post(f"/api/files/{doc.id}/process", headers=auth_headers_u2)
    assert response.status_code == 404

def test_process_empty_txt(db: Session, setup_users, auth_headers_u1):
    u1, _ = setup_users
    stored_name, path = create_mock_txt_file("   \n   ")
    
    doc = Document(
        user_id=u1.id,
        original_filename="empty.txt",
        stored_filename=stored_name,
        file_type="txt",
        mime_type="text/plain",
        file_size=10,
        storage_path=path
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    response = client.post(f"/api/files/{doc.id}/process", headers=auth_headers_u1)
    assert response.status_code == 400
    data = response.json()
    assert "TXT file is empty" in data["detail"]
    
    db.expire_all()
    db_doc = db.query(Document).filter(Document.id == doc.id).first()
    assert db_doc.processing_status == "failed"
    assert "TXT file is empty" in db_doc.processing_error

def test_process_missing_physical_file(db: Session, setup_users, auth_headers_u1):
    u1, _ = setup_users
    
    doc = Document(
        user_id=u1.id,
        original_filename="missing.txt",
        stored_filename=f"{uuid.uuid4()}_missing.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size=10,
        storage_path="invalid_path.txt"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    response = client.post(f"/api/files/{doc.id}/process", headers=auth_headers_u1)
    assert response.status_code == 404
    
    db.expire_all()
    db_doc = db.query(Document).filter(Document.id == doc.id).first()
    assert db_doc.processing_status == "failed"
    assert "missing" in db_doc.processing_error.lower()
