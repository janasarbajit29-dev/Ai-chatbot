from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_type: str
    mime_type: str
    file_size: int
    processing_status: str
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    chunks_count: Optional[int] = None

    model_config = {"from_attributes": True}
