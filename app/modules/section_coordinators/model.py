from datetime import datetime
from pydantic import BaseModel, Field

class SectionCoordinator(BaseModel):
    id: str = Field(alias="_id")
    org_id: str
    school_id: str
    
    teacher_id: str
    class_id: str
    section_id: str
    
    status: str = "active"
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
