from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest
from app.core.security import get_password_hash, verify_password
from datetime import datetime, timezone, timedelta

def verify_user_activity(db: Session, user: User) -> User:
    if user.last_active:
        now = datetime.now(timezone.utc)
        last_active = user.last_active
        
        # Ensure timezone-aware datetime for comparison
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=timezone.utc)
            
        time_since_active = now - last_active
        if time_since_active > timedelta(days=5):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to 5 days of inactivity. Please log in again."
            )
            
    # Update last_active for the current valid request
    user.last_active = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user

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

def authenticate_user(db: Session, login_data: LoginRequest) -> User:
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # Update last_active
    user.last_active = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    
    return user
