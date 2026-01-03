from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    org_id: str
    plan_id: str
    status: str = "active"
    valid_till: datetime
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
