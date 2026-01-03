from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.core.permissions import Role, Permission

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[Role] = None

class AdminUserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    permissions: List[Permission]

class AdminUserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role = Role.ADMIN
