from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid

class Class(BaseModel):
    id: str = Field(default_factory=lambda: f"cls_{uuid.uuid4().hex[:8]}", alias="_id")
    org_id: str
    school_id: str
    
    class_name: str
    class_order: int
    
    status: str = "active" # active, archived
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
