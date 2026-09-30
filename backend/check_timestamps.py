from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
u = db.query(User).filter(User.email == "janasarbajit29@gmail.com").first()
print(f"User ID: {u.id}")
print(f"Created At: {u.created_at}")
print(f"Last Active: {u.last_active}")
