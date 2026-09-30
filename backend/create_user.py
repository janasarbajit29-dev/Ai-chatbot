from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import get_password_hash
from datetime import date

from app.core.config import settings

# Use application config
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
db.query(User).filter(User.email == "real_user@example.com").delete()
db.commit()
real_user = User(
    email="real_user@example.com",
    name="Real User",
    password_hash=get_password_hash("password123"),
    date_of_birth=date(1990, 1, 1)
)
db.add(real_user)
db.commit()
print("Real user created in aura_db!")
