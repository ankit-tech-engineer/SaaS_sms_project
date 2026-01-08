from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import date, datetime

class CorrectionUser(BaseModel):
    user_id: str
    role: str

class ReviewDetails(BaseModel):
    coordinator_id: Optional[str] = None
    coordinator_remark: Optional[str] = None
    coordinator_reviewed_at: Optional[datetime] = None
    
    admin_id: Optional[str] = None
    admin_remark: Optional[str] = None
    admin_reviewed_at: Optional[datetime] = None

class AttendanceCorrectionBase(BaseModel):
    attendance_id: str
    student_id: str
    requested_status: Literal["present", "absent", "late", "half_day", "on_leave"]
    reason: str = Field(..., min_length=5, max_length=200)

class CreateCorrectionRequest(AttendanceCorrectionBase):
    pass

class CorrectionResponse(AttendanceCorrectionBase):
    id: str = Field(..., alias="_id")
    org_id: str
    school_id: str
    attendance_date: date
    academic_year: str
    old_status: str
    status: str
    requested_by: CorrectionUser
    review: ReviewDetails
    created_at: datetime
    updated_at: datetime
    
    # Enrichment fields
    class_id: Optional[str] = None
    section_id: Optional[str] = None

    class Config:
        populate_by_name = True

class CoordinatorReviewRequest(BaseModel):
    action: Literal["APPROVE", "REJECT"]
    remark: str = Field(..., min_length=2)

class AdminReviewRequest(BaseModel):
    action: Literal["APPROVE", "REJECT"]
    remark: str = Field(..., min_length=2)
