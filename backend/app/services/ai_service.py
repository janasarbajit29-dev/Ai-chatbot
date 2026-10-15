import logging

from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.message import Message

logger = logging.getLogger(__name__)

class GeminiAIService:
    PRIMARY_MODEL = "gemini-3.8-flash"
    FALLBACK_MODEL = "gemini-3.1-flash-lite"

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
        self.fallback_model = self.FALLBACK_MODEL

    @staticmethod
    def _is_503_server_error(exc: Exception) -> bool:
        if not isinstance(exc, ServerError):
            return False
        code = getattr(exc, "code", None)
        if code is None:
            code = getattr(exc, "status_code", None)
        try:
            return int(code) == 503
        except (TypeError, ValueError):
            return False

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
                contents=contents,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="LOW")
                )
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

        primary_model = self.model
        fallback_model = getattr(self, "fallback_model", self.FALLBACK_MODEL)
        current_model = primary_model
        stream_chunk_count = 0

        while True:
            try:
                history_copy = [
                    types.Content(
                        role=item.role,
                        parts=[
                            types.Part.from_text(text=part.text)
                            for part in item.parts
                            if getattr(part, "text", None) is not None
                        ]
                    )
                    for item in history
                ]
                chat = self.client.chats.create(
                    model=current_model,
                    history=history_copy,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_level="LOW")
                    )
                )
                logger.info("Gemini chat creation succeeded: model=%s", current_model)
                logger.info("Gemini stream started: model=%s", current_model)
                response_stream = chat.send_message_stream(message=latest_message)
                for chunk in response_stream:
                    if chunk.text:
                        stream_chunk_count += 1
                        yield chunk.text
                logger.info(
                    "Gemini stream completed: model=%s chunk_count=%d",
                    current_model,
                    stream_chunk_count,
                )
                return
            except Exception as exc:
                error_code = getattr(exc, "code", None)
                if error_code is None:
                    error_code = getattr(exc, "status_code", None)
                error_status = getattr(exc, "status", None)

                can_fallback = (
                    current_model == primary_model
                    and bool(fallback_model)
                    and fallback_model != primary_model
                    and stream_chunk_count == 0
                    and self._is_503_server_error(exc)
                )

                if can_fallback:
                    logger.warning(
                        "Gemini stream attempt failed: model=%s exception_type=%s error_code=%s error_status=%s chunk_count=%d safe_message=%s",
                        current_model,
                        type(exc).__name__,
                        error_code,
                        error_status,
                        stream_chunk_count,
                        f"Primary model unavailable (503); attempting fallback model {fallback_model}",
                    )
                    current_model = fallback_model
                    continue

                logger.error(
                    "Gemini stream failed: model=%s exception_type=%s error_code=%s error_status=%s chunk_count=%d safe_message=%s",
                    current_model,
                    type(exc).__name__,
                    error_code,
                    error_status,
                    stream_chunk_count,
                    "Streaming generation failed; provider details omitted",
                )
                raise

ai_service = GeminiAIService()
