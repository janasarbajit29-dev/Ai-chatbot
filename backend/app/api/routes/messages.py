from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.services import message_service

router = APIRouter(tags=["Messages"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, summary="Create a new message")
def create_message(
    conversation_id: int,
    schema: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return message_service.create_message(db, current_user.id, conversation_id, schema)

@router.get("/", response_model=List[MessageResponse], summary="Get all messages in a conversation")
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return message_service.get_conversation_messages(db, current_user.id, conversation_id)

@router.get("/{message_id}", response_model=MessageResponse, summary="Get a specific message")
def get_message(
    conversation_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return message_service.get_message_by_id(db, current_user.id, conversation_id, message_id)

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a specific message")
def delete_message(
    conversation_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    message_service.delete_message(db, current_user.id, conversation_id, message_id)
