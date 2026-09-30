from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
users = db.query(User).all()
print("Total users in aura_db:", len(users))
for u in users:
    print(f"User ID: {u.id}, Name: {u.name}, Email: {u.email}, Hash: {'YES' if u.password_hash else 'NO'}")
