from pydantic import BaseModel, Field
from app.schemas.message import MessageResponse

class ChatRequest(BaseModel):
    conversation_id: int
    content: str = Field(..., min_length=1, max_length=20000)

class ChatResponse(BaseModel):
    conversation_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse
