from google import genai
from google.genai import types
from google.genai.errors import APIError
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.message import Message

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
        try:
            contents = []
            for msg in conversation_history:
                role = "user" if msg.role in ["user", "system"] else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )

            response_stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=contents
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except APIError as e:
            # Note: Raising HTTPException inside a generator being streamed might just terminate the stream 
            # abruptly depending on the ASGI server, but it's safe and standard.
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error communicating with AI service provider."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while generating the AI response."
            )

ai_service = GeminiAIService()
