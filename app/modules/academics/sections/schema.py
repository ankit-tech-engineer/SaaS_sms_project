from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# Request Schemas
class CreateSectionRequest(BaseModel):
    section_name: str = Field(..., min_length=1, max_length=10)
    capacity: int = Field(40, ge=1, le=200)

class UpdateSectionRequest(BaseModel):
    section_name: Optional[str] = Field(None, min_length=1, max_length=10)
    capacity: Optional[int] = Field(None, ge=1, le=200)

class SectionStatusUpdate(BaseModel):
    status: str

# Response Schema
class SectionResponse(BaseModel):
    id: str = Field(alias="_id")
    class_id: str
    section_name: str
    capacity: int
    status: str
    created_at: datetime
    
    model_config = ConfigDict(populate_by_name=True)
