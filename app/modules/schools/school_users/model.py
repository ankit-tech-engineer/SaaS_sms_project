from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid

class SchoolUser(BaseModel):
    id: str = Field(default_factory=lambda: f"su_{uuid.uuid4().hex[:8]}", alias="_id")
    org_id: str
    school_id: str
    
    name: str
    email: EmailStr
    password: str # Hashed
    
    role: str = "SCHOOL_ADMIN" # SCHOOL_ADMIN, TEACHER, etc.
    permissions: List[str] = []
    
    status: str = "active" # active | suspended
    last_login_at: Optional[datetime] = None
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
