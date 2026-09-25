from typing import List, Tuple
from app.schemas.rag import RAGChunkResponse
from app.core.config import settings

def build_rag_context(chunks: List[RAGChunkResponse]) -> Tuple[str, int]:
    """
    Builds a structured context string from retrieved document chunks.
    
    Returns:
        A tuple of (context_string, chunks_used_count).
    """
    if not chunks:
        return "", 0
        
    context_parts = []
    current_length = 0
    chunks_used = 0
    
    for chunk in chunks:
        part = f"[Document {chunk.document_id} | Chunk {chunk.chunk_index}]\n{chunk.content}"
        
        if current_length + len(part) > settings.RAG_MAX_CONTEXT_CHARACTERS:
            # Prefer selecting fewer high-quality chunks over cutting them in half
            # If we haven't even added one chunk, we have to truncate the first one.
            if chunks_used == 0:
                allowed = settings.RAG_MAX_CONTEXT_CHARACTERS - current_length - 50
                if allowed > 100:
                    context_parts.append(part[:allowed] + "...\n[TRUNCATED]")
                    chunks_used += 1
            break
            
        context_parts.append(part)
        current_length += len(part)
        chunks_used += 1
        
    context_string = "\n\n".join(context_parts)
    return context_string, chunks_used
