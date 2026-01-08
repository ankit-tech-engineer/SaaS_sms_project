from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Login Request
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Token Response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any] # Basic user info to return immediately

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Profile Response
class SchoolUserResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: EmailStr
    role: str
    school_id: str
    org_id: str
    permissions: List[str]
    last_login_at: Optional[datetime]
    
    class Config:
        populate_by_name = True

# Change Password
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
