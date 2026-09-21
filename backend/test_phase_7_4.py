import os
import sys
import uuid
# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("Starting tests...")
    
    email1 = f"test_{uuid.uuid4().hex[:8]}@example.com"
    email2 = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    
    # Register user 1
    res = client.post("/api/auth/signup", json={"name": "Test User 1", "email": email1, "password": password, "confirm_password": password, "date_of_birth": "1990-01-01"})
    if res.status_code >= 400: print("Signup U1 error:", res.text)
    
    # Login user 1
    res = client.post("/api/auth/login", json={"email": email1, "password": password})
    if res.status_code >= 400: print("Login U1 error:", res.text)
    token1 = res.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    # Register user 2
    res = client.post("/api/auth/signup", json={"name": "Test User 2", "email": email2, "password": password, "confirm_password": password, "date_of_birth": "1990-01-01"})
    if res.status_code >= 400: print("Signup U2 error:", res.text)
    
    # Login user 2
    res = client.post("/api/auth/login", json={"email": email2, "password": password})
    if res.status_code >= 400: print("Login U2 error:", res.text)
    token2 = res.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create conversation for user 1
    res = client.post("/api/conversations/", json={"title": "Test Chat"}, headers=headers1)
    conv1_id = res.json()["id"]
    
    # Test unauthenticated request
    res = client.post("/api/chat/", json={"conversation_id": conv1_id, "content": "Hello"})
    print("Unauthenticated Chat:", res.status_code)
    assert res.status_code == 401
    
    # Test cross-user conversation access
    res = client.post("/api/chat/", json={"conversation_id": conv1_id, "content": "Hello"}, headers=headers2)
    print("Cross-User Chat:", res.status_code)
    assert res.status_code == 404
    
    # Test empty message validation
    res = client.post("/api/chat/", json={"conversation_id": conv1_id, "content": ""}, headers=headers1)
    print("Empty Message:", res.status_code)
    assert res.status_code == 422
    
    # Test authenticated chat request
    print("Sending real chat request to Gemini...")
    res = client.post("/api/chat/", json={"conversation_id": conv1_id, "content": "Hello AURA, say exactly 'Hello, world!'"}, headers=headers1)
    print("Real Chat:", res.status_code)
    assert res.status_code == 200
    chat_resp = res.json()
    print("User Message Saved:", chat_resp["user_message"]["content"])
    print("Assistant Message Saved:", chat_resp["assistant_message"]["content"])
    
    # Test conversation history retrieval
    res = client.get(f"/api/conversations/{conv1_id}/messages", headers=headers1)
    print("History Retrieval:", res.status_code)
    history = res.json()
    print(f"Messages in history: {len(history)}")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
