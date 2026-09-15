from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    date_of_birth: date
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None

    model_config = {"from_attributes": True}
