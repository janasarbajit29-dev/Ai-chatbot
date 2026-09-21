from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal

class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., max_length=20000)

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message content cannot be empty")
        return v

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
