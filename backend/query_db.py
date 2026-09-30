from app.database.connection import SessionLocal
from app.models.user import User

db = SessionLocal()
users = db.query(User).all()
print("Total users:", len(users))
for u in users:
    print(f"User ID: {u.id}, Name: {u.name}, Email: {u.email}, Hash length: {len(u.password_hash)}")
