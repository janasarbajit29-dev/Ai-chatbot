from sqlalchemy.orm import Session
from app.services.ai_service import ai_service
from app.services import message_service
from app.schemas.message import MessageCreate
from app.schemas.chat import ChatRequest, ChatResponse

def process_chat_message(db: Session, user_id: int, schema: ChatRequest) -> ChatResponse:
    # Save the user's message. This internally validates the conversation ownership.
    user_msg_create = MessageCreate(role="user", content=schema.content)
    user_message = message_service.create_message(db, user_id, schema.conversation_id, user_msg_create)

    # Load conversation history.
    history = message_service.get_conversation_messages(db, user_id, schema.conversation_id)

    # RAG Integration
    sources = []
    try:
        from app.services.rag_retrieval_service import retrieve_relevant_chunks
        from app.services.rag_context_service import build_rag_context
        from app.services.rag_answer_service import SYSTEM_INSTRUCTIONS, PROMPT_TEMPLATE
        from app.models.message import Message
        from app.models.document import Document

        chunks = retrieve_relevant_chunks(db, user_id, schema.content, top_k=5)
        if chunks:
            seen_docs = set()
            for c in chunks:
                if c.document_id not in seen_docs:
                    doc = db.query(Document).filter(Document.id == c.document_id).first()
                    if doc:
                        sources.append({
                            "document_id": c.document_id,
                            "filename": doc.original_filename,
                            "chunk_index": c.chunk_index,
                            "relevance": c.similarity
                        })
                        seen_docs.add(c.document_id)

            context_string, _ = build_rag_context(chunks)
            rag_prompt = PROMPT_TEMPLATE.format(
                system_instructions=SYSTEM_INSTRUCTIONS,
                user_query=schema.content,
                document_context=context_string
            )
            # Safely replace the user's question with the RAG prompt in-memory
            if history and history[-1].role == "user" and history[-1].content == schema.content:
                history[-1] = Message(role="user", content=rag_prompt)
    except Exception:
        # Fall back to normal chat safely if retrieval fails
        pass

    # Call the AI service.
    ai_response_text = ai_service.generate_response(history)

    # Save the assistant's message.
    assistant_msg_create = MessageCreate(role="assistant", content=ai_response_text)
    assistant_message = message_service.create_message(db, user_id, schema.conversation_id, assistant_msg_create)

    return ChatResponse(
        conversation_id=schema.conversation_id,
        user_message=user_message,
        assistant_message=assistant_message,
        sources=sources
    )

import json

def process_streaming_chat_message(db: Session, user_id: int, schema: ChatRequest):
    user_msg_create = MessageCreate(role="user", content=schema.content)
    user_message = message_service.create_message(db, user_id, schema.conversation_id, user_msg_create)

    history = message_service.get_conversation_messages(db, user_id, schema.conversation_id)

    # RAG Integration
    sources = []
    try:
        from app.services.rag_retrieval_service import retrieve_relevant_chunks
        from app.services.rag_context_service import build_rag_context
        from app.services.rag_answer_service import SYSTEM_INSTRUCTIONS, PROMPT_TEMPLATE
        from app.models.message import Message
        from app.models.document import Document

        chunks = retrieve_relevant_chunks(db, user_id, schema.content, top_k=5)
        if chunks:
            seen_docs = set()
            for c in chunks:
                if c.document_id not in seen_docs:
                    doc = db.query(Document).filter(Document.id == c.document_id).first()
                    if doc:
                        sources.append({
                            "document_id": c.document_id,
                            "filename": doc.original_filename,
                            "chunk_index": c.chunk_index,
                            "relevance": c.similarity
                        })
                        seen_docs.add(c.document_id)

            context_string, _ = build_rag_context(chunks)
            rag_prompt = PROMPT_TEMPLATE.format(
                system_instructions=SYSTEM_INSTRUCTIONS,
                user_query=schema.content,
                document_context=context_string
            )
            if history and history[-1].role == "user" and history[-1].content == schema.content:
                history[-1] = Message(role="user", content=rag_prompt)
    except Exception:
        pass

    # Optionally we can yield an initial event with user_message details
    yield f"data: {json.dumps({'type': 'start', 'user_message_id': user_message.id})}\n\n"

    assistant_content = ""
    try:
        for chunk in ai_service.generate_stream_response(history):
            assistant_content += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        
        assistant_msg_create = MessageCreate(role="assistant", content=assistant_content)
        assistant_message = message_service.create_message(db, user_id, schema.conversation_id, assistant_msg_create)
        
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            
        yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': 'An error occurred during generation.'})}\n\n"
