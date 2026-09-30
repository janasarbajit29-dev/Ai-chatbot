import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

print("1. Signup -> Login")
email = "verify@example.com"
password = "password123"

# Signup
signup = requests.post(f"{BASE_URL}/api/auth/signup", json={
    "name": "Verify",
    "email": email,
    "password": password,
    "confirm_password": password,
    "date_of_birth": "1990-01-01"
})
if signup.status_code not in (200, 201):
    print("Signup failed:", signup.status_code, signup.text)

# Login
login = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": email,
    "password": password
})
print("Login status:", login.status_code)

print("\n2. Wrong password returns 401")
bad_pwd = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": email,
    "password": "wrong"
})
print("Wrong password status:", bad_pwd.status_code)

print("\n3. Unknown email returns 401")
bad_email = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "unknown@example.com",
    "password": "password"
})
print("Unknown email status:", bad_email.status_code)
