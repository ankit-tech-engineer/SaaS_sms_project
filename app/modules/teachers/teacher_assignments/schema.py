from typing import List, Optional, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, model_validator
from app.core.academic_year import get_current_academic_year

# --- Request Schemas ---
class CreateAssignmentRequest(BaseModel):
    teacher_id: str
    class_id: str
    section_id: str
    subject_id: str
    academic_year: str = Field(default_factory=get_current_academic_year)
    
    role_type: Literal["PRIMARY", "CO_TEACHER", "SUBSTITUTE"] = "PRIMARY"
    substitute_from: Optional[date] = None
    substitute_to: Optional[date] = None

    @model_validator(mode='after')
    def validate_substitute_dates(self):
        if self.role_type == "SUBSTITUTE":
            if not self.substitute_from or not self.substitute_to:
                raise ValueError("Substitute period (from/to) is required for SUBSTITUTE role")
            if self.substitute_from > self.substitute_to:
                raise ValueError("Substitute start date cannot be after end date")
        return self

# --- Response Schemas ---
class AssignmentItem(BaseModel):
    assignment_id: str
    class_name: str
    section_name: str
    subject_name: str
    teacher_name: str
    role_type: str
    academic_year: str
    assigned_at: datetime

class AssignmentListResponse(BaseModel):
    success: bool
    data: List[AssignmentItem]

class AssignmentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[AssignmentItem] = None
