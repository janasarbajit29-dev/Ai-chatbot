from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.message import Message
from app.models.conversation import Conversation
from app.schemas.message import MessageCreate
from datetime import datetime, timezone

def _get_user_conversation(db: Session, user_id: int, conversation_id: int) -> Conversation:
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv or conv.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv

def create_message(db: Session, user_id: int, conversation_id: int, schema: MessageCreate) -> Message:
    conv = _get_user_conversation(db, user_id, conversation_id)
    
    new_message = Message(
        conversation_id=conversation_id,
        role=schema.role,
        content=schema.content
    )
    db.add(new_message)
    
    # Update conversation's updated_at timestamp
    conv.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(new_message)
    return new_message

def get_conversation_messages(db: Session, user_id: int, conversation_id: int) -> list[Message]:
    _get_user_conversation(db, user_id, conversation_id)
    
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

def get_message_by_id(db: Session, user_id: int, conversation_id: int, message_id: int) -> Message:
    _get_user_conversation(db, user_id, conversation_id)
    
    message = db.query(Message).filter(Message.id == message_id, Message.conversation_id == conversation_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message

def delete_message(db: Session, user_id: int, conversation_id: int, message_id: int) -> None:
    message = get_message_by_id(db, user_id, conversation_id, message_id)
    db.delete(message)
    db.commit()
