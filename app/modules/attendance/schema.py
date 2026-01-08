from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
import re
from datetime import date

# --- Shared ---
class AttendanceRecordItem(BaseModel):
    student_id: str
    status: Literal["present", "absent", "leave"]

# --- Requests ---
class MarkAttendanceRequest(BaseModel):
    class_id: str
    section_id: str
    subject_id: Optional[str] = None # Required for SUBJECT_TEACHER mode
    date: str = Field(..., description="YYYY-MM-DD")
    records: List[AttendanceRecordItem]
    
    @field_validator('date')
    def validate_date(cls, v):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

class ReviewAttendanceRequest(BaseModel):
    action: Literal["APPROVE", "REJECT"]
    remarks: Optional[str] = None

class SetPolicyRequest(BaseModel):
    mode: Literal["COORDINATOR_ONLY", "SUBJECT_TEACHER"]
    past_attendance_days_allowed: Optional[int] = 0

# --- Responses ---
class AttendanceReviewStatus(BaseModel):
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    remarks: Optional[str] = None

class AttendanceResponseData(BaseModel):
    attendance_id: str = Field(..., alias="_id")
    class_id: str
    section_id: str
    subject_id: Optional[str]
    date: str
    status: str
    locked: bool
    review: Optional[AttendanceReviewStatus] = None
    
class GenericAttendanceResponse(BaseModel):
    success: bool
    message: str
    data: Optional[AttendanceResponseData] = None

class PolicyResponse(BaseModel):
    success: bool
    mode: str
    past_attendance_days_allowed: int
