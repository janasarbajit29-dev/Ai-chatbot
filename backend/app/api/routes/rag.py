from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.database.connection import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.rag import RAGRetrieveRequest, RAGRetrieveResponse
from app.services.rag_retrieval_service import retrieve_relevant_chunks

router = APIRouter(prefix="/api/rag", tags=["rag"])

@router.post("/retrieve", response_model=RAGRetrieveResponse)
def retrieve_chunks(
    request: RAGRetrieveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Test endpoint for Phase 8.4 RAG retrieval.
    Generates embedding for query and performs vector search over user's document chunks.
    """
    try:
        results = retrieve_relevant_chunks(
            db=db,
            user_id=current_user.id,
            query=request.query,
            top_k=request.top_k
        )
        return RAGRetrieveResponse(results=results)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during retrieval: {str(e)}"
        )
