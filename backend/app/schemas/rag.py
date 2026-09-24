from pydantic import BaseModel, Field
from typing import List

class RAGRetrieveRequest(BaseModel):
    query: str = Field(..., description="The user's query to search for.")
    top_k: int = Field(5, ge=1, le=10, description="The maximum number of chunks to return.")

class RAGChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    similarity: float

class RAGRetrieveResponse(BaseModel):
    results: List[RAGChunkResponse]
