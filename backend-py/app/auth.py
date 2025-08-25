from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import logging

from .db import get_db
from .models import User, UserCreate, UserLogin, Token

logger = logging.getLogger(__name__)
router = APIRouter()

# Security
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(db, email: str):
    cursor = await db.execute(
        "SELECT id, email, password_hash, created_at, updated_at FROM users WHERE email = ?",
        (email,)
    )
    row = await cursor.fetchone()
    if row:
        return {
            "id": row["id"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
            "updated_at": datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
        }
    return None

async def get_user_by_id(db, user_id: int):
    cursor = await db.execute(
        "SELECT id, email, password_hash, created_at, updated_at FROM users WHERE id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    if row:
        return User(
            id=row["id"],
            email=row["email"],
            created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
        )
    return None

async def authenticate_user(db, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = await get_db()
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    db = await get_db()
    
    # Check if user already exists
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    
    cursor = await db.execute(
        """INSERT INTO users (email, password_hash) 
           VALUES (?, ?) RETURNING id""",
        (user.email, hashed_password)
    )
    row = await cursor.fetchone()
    await db.commit()
    
    user_id = row["id"]
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)}, expires_delta=access_token_expires
    )
    
    logger.info(f"✅ User registered: {user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db = await get_db()
    
    user_data = await authenticate_user(db, user.email, user.password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_data["id"])}, expires_delta=access_token_expires
    )
    
    logger.info(f"✅ User logged in: {user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}