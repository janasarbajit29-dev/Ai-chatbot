from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate

def create_conversation(db: Session, user_id: int, schema: ConversationCreate) -> Conversation:
    title = schema.title or "New Conversation"
    new_conv = Conversation(user_id=user_id, title=title)
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv

def get_user_conversations(db: Session, user_id: int) -> list[Conversation]:
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).all()

def get_conversation_by_id(db: Session, user_id: int, conversation_id: int) -> Conversation:
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv or conv.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv

def delete_conversation(db: Session, user_id: int, conversation_id: int) -> None:
    conv = get_conversation_by_id(db, user_id, conversation_id)
    db.delete(conv)
    db.commit()
