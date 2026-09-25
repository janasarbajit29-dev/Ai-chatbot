import os
import sys
import uuid
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("Starting Phase 7.7 Streaming Tests...")
    
    email = f"stream_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    
    client.post("/api/auth/signup", json={"name": "Stream User", "email": email, "password": password, "confirm_password": password, "date_of_birth": "1990-01-01"})
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/api/conversations/", json={"title": "Stream Conv"}, headers=headers)
    conv_id = res.json()["id"]
    
    # Test unauthenticated
    res = client.post("/api/chat/stream", json={"conversation_id": conv_id, "content": "Hello"})
    assert res.status_code == 401
    
    # Test valid streaming
    print("Sending streaming request to Gemini...")
    res = client.post(
        "/api/chat/stream", 
        json={"conversation_id": conv_id, "content": "Say 'Hi AURA'"}, 
        headers=headers
    )
    
    assert res.status_code == 200
    
    chunks = []
    final_id = None
    
    # TestClient doesn't truly "stream" over HTTP, but iter_lines still works on the returned content
    for line in res.iter_lines():
        if line:
            line_str = line
            if line_str.startswith("data: "):
                data = json.loads(line_str[6:])
                if data["type"] == "chunk":
                    chunks.append(data["content"])
                elif data["type"] == "done":
                    final_id = data["message_id"]
                    
    response_text = "".join(chunks)
    print("Accumulated response:", response_text)
    assert len(chunks) > 0
    assert final_id is not None
    
    # Verify persistence
    res = client.get(f"/api/conversations/{conv_id}/messages", headers=headers)
    history = res.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[1]["id"] == final_id
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
