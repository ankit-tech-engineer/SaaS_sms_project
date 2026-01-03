from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid

class Subject(BaseModel):
    id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:8]}", alias="_id")
    org_id: str
    school_id: str
    class_id: str
    
    subject_name: str
    subject_code: str
    is_optional: bool = False
    
    status: str = "active" # active, archived
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
