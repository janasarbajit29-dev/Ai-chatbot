from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import generate_query_embedding
from app.schemas.rag import RAGChunkResponse

def retrieve_relevant_chunks(db: Session, user_id: int, query: str, top_k: int = 5) -> List[RAGChunkResponse]:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
        
    if top_k < 1 or top_k > 10:
        raise ValueError("top_k must be between 1 and 10.")
        
    # Generate query embedding
    try:
        query_embedding = generate_query_embedding(query)
    except Exception as e:
        raise ValueError(f"Failed to generate query embedding: {str(e)}")

    # Perform vector similarity search
    # We use cosine distance: DocumentChunk.embedding.cosine_distance(query_embedding)
    # Cosine similarity = 1 - cosine distance
    distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
    
    from app.models.document import Document
    from app.core.config import settings
    
    max_distance = 1.0 - settings.RAG_SIMILARITY_THRESHOLD
    
    stmt = (
        select(DocumentChunk, distance_expr.label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.user_id == user_id,
            Document.processing_status == "ready",
            distance_expr <= max_distance
        )
        .order_by(distance_expr)
        .limit(top_k * 3)  # fetch more candidates for deduplication
    )
    
    results = db.execute(stmt).all()
    
    response_chunks = []
    doc_chunk_counts = {}
    
    for row in results:
        if len(response_chunks) >= top_k:
            break
            
        chunk = row[0]
        distance = row.distance
        similarity = 1.0 - distance
        
        # Lightweight deduplication: Prevent one document from dominating the context
        count = doc_chunk_counts.get(chunk.document_id, 0)
        if count >= 3:
            continue
            
        doc_chunk_counts[chunk.document_id] = count + 1
        
        response_chunks.append(
            RAGChunkResponse(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=similarity
            )
        )
        
    return response_chunks
