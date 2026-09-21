from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
