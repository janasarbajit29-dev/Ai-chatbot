from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services import document_service, document_processing_service

router = APIRouter(tags=["Files"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, summary="Upload a secure file")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return document_service.save_document(db, current_user.id, file)

@router.post("/{file_id}/process", response_model=DocumentResponse, summary="Process document and extract text")
def process_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return document_processing_service.process_document(db, file_id, current_user.id)

@router.get("/", response_model=List[DocumentResponse], summary="Get user files")
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return document_service.get_user_documents(db, current_user.id)

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a file")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document_service.delete_document(db, current_user.id, file_id)
