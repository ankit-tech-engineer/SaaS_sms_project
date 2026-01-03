from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    org_name: str
    owner_name: str
    owner_user_id: Optional[str] = None
    email: EmailStr
    mobile: str
    plan_id: Optional[str] = None
    trial_days: int = 14
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
