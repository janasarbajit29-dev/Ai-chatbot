from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationUpdate
from app.services import conversation_service

router = APIRouter(tags=["Conversations"])

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, summary="Create a new conversation")
def create_conversation(
    schema: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return conversation_service.create_conversation(db, current_user.id, schema)

@router.get("/", response_model=List[ConversationResponse], summary="Get all conversations for the current user")
def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return conversation_service.get_user_conversations(db, current_user.id)

@router.get("/{conversation_id}", response_model=ConversationResponse, summary="Get a specific conversation")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return conversation_service.get_conversation_by_id(db, current_user.id, conversation_id)

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a specific conversation")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation_service.delete_conversation(db, current_user.id, conversation_id)

@router.patch("/{conversation_id}", response_model=ConversationResponse, summary="Update a specific conversation")
def update_conversation(
    conversation_id: int,
    schema: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return conversation_service.update_conversation(db, current_user.id, conversation_id, schema)
