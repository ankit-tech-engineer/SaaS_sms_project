from pydantic import BaseModel
from datetime import date

class SubscriptionAssignRequest(BaseModel):
    org_id: str
    plan_id: str

class SubscriptionAssignResponse(BaseModel):
    subscription_id: str
    status: str
    valid_till: date
