import json
import logging
from types import SimpleNamespace

import pytest
from google.genai.errors import ClientError, ServerError
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


def test_stream_logs_provider_error_diagnostics_on_server_error(caplog):
    class FailingChat:
        def send_message_stream(self, **kwargs):
            raise ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE", "message": "This model is currently experiencing high demand."}},
            )

    class MockChats:
        def create(self, **kwargs):
            return FailingChat()

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "test-model"
    messages = [SimpleNamespace(role="user", content="Hello")]

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ServerError):
            list(service.generate_stream_response(messages))

    assert "Gemini stream failed" in caplog.text
    assert "exception_type=ServerError" in caplog.text
    assert "error_code=503" in caplog.text
    assert "error_status=UNAVAILABLE" in caplog.text
    assert "chunk_count=0" in caplog.text
    assert "safe_message=Streaming generation failed; provider details omitted" in caplog.text


def test_stream_primary_succeeds_without_fallback():
    create_calls = []

    class MockChat:
        def send_message_stream(self, **kwargs):
            return iter([SimpleNamespace(text="Primary "), SimpleNamespace(text="success")])

    class MockChats:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            return MockChat()

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "gemini-3.8-flash"
    service.fallback_model = "gemini-3.1-flash-lite"
    messages = [SimpleNamespace(role="user", content="Hello")]

    chunks = list(service.generate_stream_response(messages))

    assert chunks == ["Primary ", "success"]
    assert len(create_calls) == 1
    assert create_calls[0]["model"] == "gemini-3.8-flash"
    thinking_level = str(create_calls[0]["config"].thinking_config.thinking_level)
    assert "LOW" in thinking_level


def test_stream_primary_503_before_first_chunk_fallback_succeeds(caplog):
    create_calls = []
    send_calls = []

    class PrimaryFailingChat:
        def send_message_stream(self, **kwargs):
            send_calls.append(("primary", kwargs))
            def failing_gen():
                raise ServerError(
                    503,
                    {"error": {"code": 503, "status": "UNAVAILABLE", "message": "Primary high demand"}},
                )
                yield
            return failing_gen()

    class FallbackWorkingChat:
        def send_message_stream(self, **kwargs):
            send_calls.append(("fallback", kwargs))
            return iter([SimpleNamespace(text="Fallback "), SimpleNamespace(text="chunk")])

    class MockChats:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            if kwargs["model"] == "gemini-3.8-flash":
                return PrimaryFailingChat()
            return FallbackWorkingChat()

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "gemini-3.8-flash"
    service.fallback_model = "gemini-3.1-flash-lite"
    messages = [
        SimpleNamespace(role="user", content="Earlier query"),
        SimpleNamespace(role="assistant", content="Earlier response"),
        SimpleNamespace(role="user", content="Latest query"),
    ]

    with caplog.at_level(logging.WARNING):
        chunks = list(service.generate_stream_response(messages))

    assert chunks == ["Fallback ", "chunk"]
    assert len(create_calls) == 2
    assert create_calls[0]["model"] == "gemini-3.8-flash"
    assert create_calls[1]["model"] == "gemini-3.1-flash-lite"
    assert "LOW" in str(create_calls[1]["config"].thinking_config.thinking_level)

    # Check safe warning log for primary model failure
    assert "Gemini stream attempt failed" in caplog.text
    assert "model=gemini-3.8-flash" in caplog.text
    assert "exception_type=ServerError" in caplog.text
    assert "error_code=503" in caplog.text
    assert "error_status=UNAVAILABLE" in caplog.text
    assert "chunk_count=0" in caplog.text
    assert "attempting fallback model gemini-3.1-flash-lite" in caplog.text

    # Verify sends
    assert len(send_calls) == 2
    assert send_calls[0] == ("primary", {"message": "Latest query"})
    assert send_calls[1] == ("fallback", {"message": "Latest query"})


def test_stream_both_models_fail_safely(caplog):
    create_calls = []

    class FailingChat:
        def __init__(self, name):
            self.name = name

        def send_message_stream(self, **kwargs):
            raise ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE", "message": f"{self.name} overloaded"}},
            )

    class MockChats:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            return FailingChat(kwargs["model"])

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "gemini-3.8-flash"
    service.fallback_model = "gemini-3.1-flash-lite"
    messages = [SimpleNamespace(role="user", content="Hello")]

    with caplog.at_level(logging.WARNING):
        with pytest.raises(ServerError):
            list(service.generate_stream_response(messages))

    assert len(create_calls) == 2
    assert create_calls[0]["model"] == "gemini-3.8-flash"
    assert create_calls[1]["model"] == "gemini-3.1-flash-lite"

    # Both warning (for primary) and error (for fallback) logged safely
    assert "model=gemini-3.8-flash" in caplog.text
    assert "model=gemini-3.1-flash-lite" in caplog.text
    assert "error_code=503" in caplog.text
    assert "safe_message=Streaming generation failed; provider details omitted" in caplog.text


def test_stream_primary_fails_after_yielding_chunk_no_fallback(caplog):
    create_calls = []

    class YieldThenFailChat:
        def send_message_stream(self, **kwargs):
            def stream_gen():
                yield SimpleNamespace(text="first chunk")
                raise ServerError(
                    503,
                    {"error": {"code": 503, "status": "UNAVAILABLE", "message": "Mid-stream disconnect"}},
                )
            return stream_gen()

    class MockChats:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            return YieldThenFailChat()

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "gemini-3.8-flash"
    service.fallback_model = "gemini-3.1-flash-lite"
    messages = [SimpleNamespace(role="user", content="Stream me")]

    yielded = []
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ServerError):
            for chunk in service.generate_stream_response(messages):
                yielded.append(chunk)

    assert yielded == ["first chunk"]
    # Fallback must NOT be attempted because chunks were already yielded!
    assert len(create_calls) == 1
    assert create_calls[0]["model"] == "gemini-3.8-flash"
    assert "model=gemini-3.8-flash" in caplog.text
    assert "chunk_count=1" in caplog.text
    assert "safe_message=Streaming generation failed; provider details omitted" in caplog.text


def test_stream_primary_non_503_error_no_fallback(caplog):
    create_calls = []

    class ClientErrorChat:
        def send_message_stream(self, **kwargs):
            raise ClientError(
                400,
                {"error": {"code": 400, "status": "INVALID_ARGUMENT", "message": "Bad request"}},
            )

    class MockChats:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            return ClientErrorChat()

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "gemini-3.8-flash"
    service.fallback_model = "gemini-3.1-flash-lite"
    messages = [SimpleNamespace(role="user", content="Bad request")]

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ClientError):
            list(service.generate_stream_response(messages))

    # Fallback should only trigger on 503, not 400!
    assert len(create_calls) == 1
    assert create_calls[0]["model"] == "gemini-3.8-flash"
    assert "model=gemini-3.8-flash" in caplog.text
    assert "exception_type=ClientError" in caplog.text
    assert "error_code=400" in caplog.text


def test_stream_history_and_latest_message_no_duplication_across_fallback():
    create_calls = []
    send_calls = []

    class FailingChat:
        def send_message_stream(self, **kwargs):
            send_calls.append(("primary", kwargs))
            raise ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE", "message": "Busy"}},
            )

    class WorkingChat:
        def send_message_stream(self, **kwargs):
            send_calls.append(("fallback", kwargs))
            return iter([SimpleNamespace(text="ok")])

    class MockChats:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            if kwargs["model"] == "gemini-3.8-flash":
                return FailingChat()
            return WorkingChat()

    service = GeminiAIService.__new__(GeminiAIService)
    service.client = SimpleNamespace(chats=MockChats())
    service.model = "gemini-3.8-flash"
    service.fallback_model = "gemini-3.1-flash-lite"

    messages = [
        SimpleNamespace(role="assistant", content="orphaned initial assistant"),
        SimpleNamespace(role="user", content="Turn 1 user"),
        SimpleNamespace(role="assistant", content="Turn 1 assistant"),
        SimpleNamespace(role="user", content="Turn 2 incomplete user"),
        SimpleNamespace(role="user", content="Turn 3 RAG prompt"),
    ]

    chunks = list(service.generate_stream_response(messages))
    assert chunks == ["ok"]

    assert len(create_calls) == 2
    for call in create_calls:
        history = call["history"]
        # History must contain only completed previous turns
        assert [(item.role, item.parts[0].text) for item in history] == [
            ("user", "Turn 1 user"),
            ("model", "Turn 1 assistant"),
        ]
        # Latest message must NOT be in history
        for item in history:
            for part in item.parts:
                assert part.text != "Turn 3 RAG prompt"

    # Both attempts must receive the latest message exactly once via send_message_stream
    assert len(send_calls) == 2
    assert send_calls[0] == ("primary", {"message": "Turn 3 RAG prompt"})
    assert send_calls[1] == ("fallback", {"message": "Turn 3 RAG prompt"})


def test_chat_service_streaming_with_503_fallback(monkeypatch):
    from app.services.chat_service import process_streaming_chat_message
    from app.schemas.chat import ChatRequest
    from app.services.ai_service import ai_service
    from app.models.message import Message

    schema = ChatRequest(conversation_id=42, content="Test message")
    user_id = 1
    mock_db = SimpleNamespace()

    saved_messages = []

    def mock_create_message(db, uid, cid, msg_create):
        msg = SimpleNamespace(id=202, role=msg_create.role, content=msg_create.content)
        saved_messages.append(msg)
        return msg

    def mock_get_messages(db, uid, cid):
        return [Message(role="user", content="Test message")]

    monkeypatch.setattr("app.services.message_service.create_message", mock_create_message)
    monkeypatch.setattr("app.services.message_service.get_conversation_messages", mock_get_messages)

    create_calls = []

    class FailingChat:
        def send_message_stream(self, **kwargs):
            raise ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE", "message": "Primary busy"}},
            )

    class WorkingChat:
        def send_message_stream(self, **kwargs):
            return iter([SimpleNamespace(text="Fallback "), SimpleNamespace(text="worked!")])

    class MockChats:
        def create(self, **kwargs):
            create_calls.append(kwargs["model"])
            if kwargs["model"] == ai_service.model:
                return FailingChat()
            return WorkingChat()

    monkeypatch.setattr(ai_service, "client", SimpleNamespace(chats=MockChats()))

    events = []
    for line in process_streaming_chat_message(mock_db, user_id, schema):
        if line.startswith("data: "):
            events.append(json.loads(line[6:].strip()))

    event_types = [e["type"] for e in events]
    assert event_types == ["start", "chunk", "chunk", "done"]
    chunk_texts = [e["content"] for e in events if e["type"] == "chunk"]
    assert "".join(chunk_texts) == "Fallback worked!"
    assert create_calls == [ai_service.model, ai_service.fallback_model]
    assert any(m.role == "assistant" and m.content == "Fallback worked!" for m in saved_messages)


def test_chat_service_streaming_both_fail_emits_safe_error_event(monkeypatch):
    from app.services.chat_service import process_streaming_chat_message
    from app.schemas.chat import ChatRequest
    from app.services.ai_service import ai_service
    from app.models.message import Message

    schema = ChatRequest(conversation_id=42, content="Test message")
    user_id = 1
    mock_db = SimpleNamespace()

    def mock_create_message(db, uid, cid, msg_create):
        return SimpleNamespace(id=101, role=msg_create.role, content=msg_create.content)

    def mock_get_messages(db, uid, cid):
        return [Message(role="user", content="Test message")]

    monkeypatch.setattr("app.services.message_service.create_message", mock_create_message)
    monkeypatch.setattr("app.services.message_service.get_conversation_messages", mock_get_messages)

    class FailingChat:
        def send_message_stream(self, **kwargs):
            raise ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE", "message": "All busy"}},
            )

    class MockChats:
        def create(self, **kwargs):
            return FailingChat()

    monkeypatch.setattr(ai_service, "client", SimpleNamespace(chats=MockChats()))

    events = []
    for line in process_streaming_chat_message(mock_db, user_id, schema):
        if line.startswith("data: "):
            events.append(json.loads(line[6:].strip()))

    event_types = [e["type"] for e in events]
    assert event_types == ["start", "error"]
    error_event = next(e for e in events if e["type"] == "error")
    assert error_event["content"] == "An error occurred during generation."
