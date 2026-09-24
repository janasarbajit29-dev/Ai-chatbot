from typing import List
from google import genai
from google.genai import types
from app.core.config import settings

def get_genai_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of text chunks using Google GenAI SDK.
    """
    if not chunks:
        return []

    client = get_genai_client()
    
    try:
        embeddings = []
        for chunk in chunks:
            response = client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=chunk,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            if response and response.embeddings:
                embeddings.append(response.embeddings[0].values)
            else:
                raise ValueError("No embeddings returned from the API for a chunk.")
                
        return embeddings
    except Exception as e:
        raise ValueError(f"Failed to generate embeddings: {str(e)}")

def generate_query_embedding(query: str) -> List[float]:
    """
    Generates a single embedding for a retrieval query.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
        
    client = get_genai_client()
    try:
        response = client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
        if response and response.embeddings:
            return response.embeddings[0].values
        raise ValueError("No embeddings returned from the API for the query.")
    except Exception as e:
        raise ValueError(f"Failed to generate query embedding: {str(e)}")
