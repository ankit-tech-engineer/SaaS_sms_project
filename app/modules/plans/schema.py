from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class PlanCreate(BaseModel):
    plan_name: str
    price: float
    billing_cycle: str
    limits: Dict[str, Any]
    features: Dict[str, bool]

class PlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    price: Optional[float] = None
    billing_cycle: Optional[str] = None
    limits: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, bool]] = None
    is_active: Optional[bool] = None

class PlanResponse(BaseModel):
    id: str
    name: str = Field(alias="plan_name")
    price: float
    billing_cycle: str
    limits: Dict[str, Any]
    features: Dict[str, bool]
    is_active: bool
    created_at: datetime
    status: str = "created"  # Keeping for backward combatibility with create response, though maybe less relevant for read

class PlanCreateResponse(BaseModel):
    id: str
    status: str = "created"
