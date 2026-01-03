from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import uuid

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    subscription_id: str
    transaction_id: str
    amount: float
    status: str
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
