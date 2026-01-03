from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: str = Field(alias="_id")
    method: str
    url: str
    client: str
    status_code: int
    process_time: float
    timestamp: float
    user_id: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)

class AuditLogList(BaseModel):
    items: list[AuditLogResponse]
    total: int
