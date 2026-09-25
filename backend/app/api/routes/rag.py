from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.database.connection import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.rag import RAGRetrieveRequest, RAGRetrieveResponse, RAGAnswerRequest, RAGAnswerResponse
from app.services.rag_retrieval_service import retrieve_relevant_chunks
from app.services.rag_answer_service import generate_rag_answer

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

@router.post("/answer", response_model=RAGAnswerResponse)
def answer_question(
    request: RAGAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Test endpoint for Phase 8.5 RAG Answer Generation.
    Retrieves relevant document chunks and uses Gemini to answer the question.
    """
    try:
        chunks = retrieve_relevant_chunks(
            db=db,
            user_id=current_user.id,
            query=request.query,
            top_k=request.top_k
        )
        
        response = generate_rag_answer(
            query=request.query,
            chunks=chunks
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during answer generation: {str(e)}"
        )
