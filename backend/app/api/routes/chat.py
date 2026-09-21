from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(tags=["Chat"])

from fastapi.responses import StreamingResponse

@router.post("/", response_model=ChatResponse, summary="Send a message to the AI and get a response")
def chat(
    schema: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return chat_service.process_chat_message(db, current_user.id, schema)

@router.post("/stream", summary="Stream a message response from the AI")
def stream_chat(
    schema: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return StreamingResponse(
        chat_service.process_streaming_chat_message(db, current_user.id, schema),
        media_type="text/event-stream"
    )
