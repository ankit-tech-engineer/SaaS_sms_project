from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid

class Plan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str  # e.g., PRO, ENTERPRISE
    price: float
    billing_cycle: str  # monthly, yearly
    limits: Dict[str, Any]  # {max_schools: 5, ...}
    features: Dict[str, bool] # {attendance: true, ...}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
