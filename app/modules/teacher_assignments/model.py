from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field

class SubstitutePeriod(BaseModel):
    start_date: date = Field(alias="from")
    end_date: date = Field(alias="to")

    class Config:
        populate_by_name = True

class TeacherAssignment(BaseModel):
    id: str = Field(alias="_id")
    
    org_id: str
    school_id: str
    
    teacher_id: str
    class_id: str
    section_id: str
    subject_id: str
    
    academic_year: str # e.g. "2025-26"
    
    role_type: Literal["PRIMARY", "CO_TEACHER", "SUBSTITUTE"]
    substitute_period: Optional[SubstitutePeriod] = None
    
    status: str = "active" # active | inactive
    
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: str # User ID of the admin who created this
    
    class Config:
        populate_by_name = True
