from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class OrgSignupRequest(BaseModel):
    org_name: str
    owner_name: str
    email: EmailStr
    password: str
    mobile: str

class OrgUpdate(BaseModel):
    org_name: Optional[str] = None
    owner_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    status: Optional[str] = None
    trial_days: Optional[int] = None

class OrgResponse(BaseModel):
    id: str
    org_name: str
    owner_name: str
    email: EmailStr
    mobile: str
    trial_days: int
    status: str
    plan_id: Optional[str] = None
    created_at: datetime
    
class OrgSignupResponse(BaseModel):
    org_id: str
    owner_user_id: str
    trial_days: int
    status: str
