from pydantic import BaseModel, Field
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_type: str
    mime_type: str
    file_size: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
