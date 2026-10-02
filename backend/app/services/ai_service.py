import logging

from google import genai
from google.genai import types
from google.genai.errors import APIError
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.message import Message

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def generate_response(self, conversation_history: list[Message]) -> str:
        try:
            contents = []
            for msg in conversation_history:
                # Map standard roles to Gemini roles
                role = "user" if msg.role in ["user", "system"] else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            return response.text
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error communicating with AI service provider."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while generating the AI response."
            )

    def generate_stream_response(self, conversation_history: list[Message]):
        stream_chunk_count = 0
        try:
            latest_user_index = next(
                (index for index in range(len(conversation_history) - 1, -1, -1)
                 if conversation_history[index].role == "user"),
                None,
            )
            if latest_user_index is None:
                raise ValueError("Streaming requires a latest user message")

            latest_message = conversation_history[latest_user_index].content
            previous_messages = conversation_history[:latest_user_index]
            history = []
            expected_role = "user"
            for msg in previous_messages:
                if msg.role != expected_role:
                    continue

                gemini_role = "user" if msg.role == "user" else "model"
                history.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )
                expected_role = "assistant" if msg.role == "user" else "user"

            if expected_role == "assistant":
                history.pop()

            logger.info(
                "Preparing Gemini stream: history_count=%d latest_user_excluded=%s",
                len(history),
                True,
            )

            chat = self.client.chats.create(
                model=self.model,
                history=history,
            )
            logger.info("Gemini chat creation succeeded")
            logger.info("Gemini stream started")
            response_stream = chat.send_message_stream(message=latest_message)
            for chunk in response_stream:
                if chunk.text:
                    stream_chunk_count += 1
                    yield chunk.text
            logger.info(
                "Gemini stream completed: chunk_count=%d",
                stream_chunk_count,
            )
        except Exception as exc:
            logger.error(
                "Gemini stream failed: exception_type=%s chunk_count=%d safe_message=%s",
                type(exc).__name__,
                stream_chunk_count,
                "Streaming generation failed; provider details omitted",
            )
            raise

ai_service = GeminiAIService()
