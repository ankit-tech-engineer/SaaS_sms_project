from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from app.core.config import settings

# Specific pwd_context for Teacher Users
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use a specific secret key for teachers
TEACHER_SECRET_KEY = getattr(settings, "TEACHER_SECRET_KEY", settings.SECRET_KEY + "_teacher") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.TEACHER_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7 # 7 Days

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], extra_claims: dict = None, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"sub": str(subject), "type": "TEACHER_USER"}
    if extra_claims:
        to_encode.update(extra_claims)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, TEACHER_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
    to_encode = {"sub": str(subject), "type": "TEACHER_REFRESH_TOKEN"}
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, TEACHER_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, TEACHER_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "TEACHER_USER":
            return None
        return payload
    except jwt.JWTError:
        return None

def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, TEACHER_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "TEACHER_REFRESH_TOKEN":
            return None
        return payload
    except jwt.JWTError:
        return None
