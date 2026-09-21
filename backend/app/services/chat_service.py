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

    # Call the AI service.
    ai_response_text = ai_service.generate_response(history)

    # Save the assistant's message.
    assistant_msg_create = MessageCreate(role="assistant", content=ai_response_text)
    assistant_message = message_service.create_message(db, user_id, schema.conversation_id, assistant_msg_create)

    return ChatResponse(
        conversation_id=schema.conversation_id,
        user_message=user_message,
        assistant_message=assistant_message
    )

import json

def process_streaming_chat_message(db: Session, user_id: int, schema: ChatRequest):
    user_msg_create = MessageCreate(role="user", content=schema.content)
    user_message = message_service.create_message(db, user_id, schema.conversation_id, user_msg_create)

    history = message_service.get_conversation_messages(db, user_id, schema.conversation_id)

    # Optionally we can yield an initial event with user_message details
    yield f"data: {json.dumps({'type': 'start', 'user_message_id': user_message.id})}\n\n"

    assistant_content = ""
    try:
        for chunk in ai_service.generate_stream_response(history):
            assistant_content += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        
        assistant_msg_create = MessageCreate(role="assistant", content=assistant_content)
        assistant_message = message_service.create_message(db, user_id, schema.conversation_id, assistant_msg_create)
        
        yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': 'An error occurred during generation.'})}\n\n"
