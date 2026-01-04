from datetime import datetime
from pydantic import BaseModel, Field

class TeacherSecurity(BaseModel):
    force_password_change: bool = True
    password_changed_at: datetime = None

class TeacherUser(BaseModel):
    id: str = Field(alias="_id")
    org_id: str
    school_id: str
    teacher_id: str
    
    username: str
    password: str # Hashed
    
    role: str = "TEACHER"
    status: str = "active"
    
    security: TeacherSecurity
    
    last_login_at: datetime = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
