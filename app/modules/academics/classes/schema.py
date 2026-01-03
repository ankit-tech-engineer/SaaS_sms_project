from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# Request Schemas
class CreateClassRequest(BaseModel):
    class_name: str = Field(..., min_length=1, max_length=20)
    class_order: int = Field(..., ge=1, le=100)

class UpdateClassRequest(BaseModel):
    class_name: Optional[str] = Field(None, min_length=1, max_length=20)
    class_order: Optional[int] = Field(None, ge=1, le=100)

class ClassStatusUpdate(BaseModel):
    status: str

# Response Schema
class ClassResponse(BaseModel):
    id: str = Field(alias="_id")
    class_name: str
    class_order: int
    status: str
    created_at: datetime
    
    model_config = ConfigDict(populate_by_name=True)
