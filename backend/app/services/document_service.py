import os
import uuid
import shutil
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from app.models.document import Document

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def save_document(db: Session, user_id: int, file: UploadFile) -> Document:
    # Read first chunk to check size early if possible, though we can't easily rely on content-length
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large. Maximum size is 10MB.")

    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type.")

    file_type = ALLOWED_MIME_TYPES[mime_type]
    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1].lower()
    
    # Also double check extension matches
    valid_exts = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}
    if ext not in valid_exts or valid_exts[ext] != file_type:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File extension does not match content type.")
        
    # Check for duplicate document
    existing_doc = db.query(Document).filter(
        Document.user_id == user_id,
        Document.original_filename == original_filename,
        Document.file_size == file_size
    ).first()
    
    if existing_doc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A document with this name and size already exists.")

    stored_filename = f"{uuid.uuid4()}{ext}"
    storage_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_doc = Document(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size=file_size,
        storage_path=storage_path
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc

def get_user_documents(db: Session, user_id: int) -> list[Document]:
    return db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all()

def delete_document(db: Session, user_id: int, document_id: int) -> None:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Remove physical file safely
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except OSError:
            pass # We ignore physical deletion errors to avoid breaking DB state if file is somehow missing/locked
    
    db.delete(doc)
    db.commit()
