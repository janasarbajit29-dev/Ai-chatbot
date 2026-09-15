from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import SignupRequest
from app.core.security import get_password_hash

def create_user(db: Session, user_in: SignupRequest) -> User:
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_in.password)
    
    # Create new user instance
    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_password,
        date_of_birth=user_in.date_of_birth,
    )
    
    # Save to db
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
