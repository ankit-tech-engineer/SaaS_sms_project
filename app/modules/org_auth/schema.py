from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class OrgUserCreate(BaseModel):
    org_id: str
    name: str
    email: EmailStr
    password: str
    mobile: str
    role: str = "ORG_OWNER"

class OrgLogin(BaseModel):
    email: EmailStr
    password: str

class OrgTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class OrgProfile(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    org_id: str
    permissions: List[str]
    status: str
    last_login_at: Optional[datetime]
    created_at: datetime
