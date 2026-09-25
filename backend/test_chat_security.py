import os
import sys
import uuid
# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("Starting Phase 7.5 Tests...")
    
    email_a = f"test_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    
    # TEST 1 & 2: Create User A & B
    client.post("/api/auth/signup", json={"name": "User A", "email": email_a, "password": password, "confirm_password": password, "date_of_birth": "1990-01-01"})
    client.post("/api/auth/signup", json={"name": "User B", "email": email_b, "password": password, "confirm_password": password, "date_of_birth": "1990-01-01"})
    
    # TEST 3: Authenticate both users
    res_a = client.post("/api/auth/login", json={"email": email_a, "password": password})
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    res_b = client.post("/api/auth/login", json={"email": email_b, "password": password})
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # TEST 4: User A creates Conversation A
    res = client.post("/api/conversations/", json={"title": "Conv A"}, headers=headers_a)
    conv_a_id = res.json()["id"]
    
    # TEST 5: User B creates Conversation B
    res = client.post("/api/conversations/", json={"title": "Conv B"}, headers=headers_b)
    conv_b_id = res.json()["id"]
    
    # TEST 6: User A lists conversations
    res = client.get("/api/conversations/", headers=headers_a)
    convs_a = res.json()
    assert len(convs_a) == 1
    assert convs_a[0]["id"] == conv_a_id
    
    # TEST 7: User B lists conversations
    res = client.get("/api/conversations/", headers=headers_b)
    convs_b = res.json()
    assert len(convs_b) == 1
    assert convs_b[0]["id"] == conv_b_id
    
    # TEST 8: User A sends real Gemini chat message to Conv A
    print("Sending real chat request to Gemini...")
    res = client.post("/api/chat/", json={"conversation_id": conv_a_id, "content": "Hello AURA! Respond with exactly 'Hi!'"}, headers=headers_a)
    assert res.status_code == 200
    
    # TEST 9: Verify both messages exist in the response
    chat_resp = res.json()
    assert chat_resp["user_message"]["role"] == "user"
    assert chat_resp["assistant_message"]["role"] == "assistant"
    print("Assistant response:", chat_resp["assistant_message"]["content"])
    
    # TEST 10: User A retrieves Conversation A history
    res = client.get(f"/api/conversations/{conv_a_id}/messages", headers=headers_a)
    history_a = res.json()
    assert len(history_a) == 2
    
    # TEST 11: User A attempts to access Conversation B
    res = client.get(f"/api/conversations/{conv_b_id}/messages", headers=headers_a)
    assert res.status_code == 404
    
    # TEST 12: User A attempts to send message to Conversation B
    res = client.post("/api/chat/", json={"conversation_id": conv_b_id, "content": "Intrusion attempt"}, headers=headers_a)
    assert res.status_code == 404
    
    # TEST 13: User A attempts to delete Conversation B
    res = client.delete(f"/api/conversations/{conv_b_id}", headers=headers_a)
    assert res.status_code == 404
    
    # TEST 14: User A refreshes/reloads and retrieves Conversation A again
    res = client.get(f"/api/conversations/{conv_a_id}/messages", headers=headers_a)
    history_a_again = res.json()
    assert len(history_a_again) == 2
    
    # TEST 15: Delete Conversation A and verify messages are removed
    res = client.delete(f"/api/conversations/{conv_a_id}", headers=headers_a)
    assert res.status_code == 204
    # Optional: Verify it's gone
    res = client.get(f"/api/conversations/{conv_a_id}/messages", headers=headers_a)
    assert res.status_code == 404
    
    # TEST 16: Unauthenticated request
    res = client.get("/api/conversations/")
    assert res.status_code == 401
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
