from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# Request Schemas
class CreateSubjectRequest(BaseModel):
    subject_name: str = Field(..., min_length=1, max_length=50)
    subject_code: str = Field(..., min_length=1, max_length=10) # e.g. MATH101
    is_optional: bool = False

class UpdateSubjectRequest(BaseModel):
    subject_name: Optional[str] = Field(None, min_length=1, max_length=50)
    subject_code: Optional[str] = Field(None, min_length=1, max_length=10)
    is_optional: Optional[bool] = None

class SubjectStatusUpdate(BaseModel):
    status: str

# Response Schema
class SubjectResponse(BaseModel):
    id: str = Field(alias="_id")
    class_id: str
    subject_name: str
    subject_code: str
    is_optional: bool
    status: str
    created_at: datetime
    
    model_config = ConfigDict(populate_by_name=True)
