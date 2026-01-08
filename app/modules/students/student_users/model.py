from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class StudentSecurity(BaseModel):
    force_password_change: bool = True
    password_changed_at: Optional[datetime] = None

class StudentUser(BaseModel):
    id: str = Field(alias="_id")
    org_id: str
    school_id: str
    student_id: str
    username: str
    password: str
    role: str = "STUDENT"
    status: str = "active"
    security: StudentSecurity
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
