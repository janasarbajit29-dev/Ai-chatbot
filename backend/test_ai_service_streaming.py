from types import SimpleNamespace

from app.services.ai_service import GeminiAIService


def test_stream_sends_latest_rag_prompt_once_with_completed_history():
    calls = {}

    class MockChat:
        def send_message_stream(self, **kwargs):
            calls["send"] = kwargs
            return iter([SimpleNamespace(text="answer "), SimpleNamespace(text="chunk")])

    class MockChats:
        def create(self, **kwargs):
            calls["create"] = kwargs
            return MockChat()

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "test-model"
    messages = [
        SimpleNamespace(role="assistant", content="orphaned prior answer"),
        SimpleNamespace(role="user", content="prior question"),
        SimpleNamespace(role="assistant", content="prior answer"),
        SimpleNamespace(role="user", content="incomplete prior turn"),
        SimpleNamespace(role="user", content="RAG-modified latest prompt"),
    ]

    chunks = list(service.generate_stream_response(messages))

    assert chunks == ["answer ", "chunk"]
    assert calls["send"] == {"message": "RAG-modified latest prompt"}
    history = calls["create"]["history"]
    assert [(item.role, item.parts[0].text) for item in history] == [
        ("user", "prior question"),
        ("model", "prior answer"),
    ]
    assert all(
        part.text != "RAG-modified latest prompt"
        for item in history
        for part in item.parts
    )