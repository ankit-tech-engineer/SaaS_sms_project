from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re

class CreateHolidayRequest(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2025-08-15")
    name: str = Field(..., min_length=2, max_length=100)
    type: Literal["NATIONAL", "FESTIVAL", "SCHOOL_EVENT"]

    @field_validator('date')
    def validate_date_format(cls, v):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

class HolidayItem(BaseModel):
    id: str = Field(..., alias="_id")
    date: str
    name: str
    type: str
    status: str
    school_id: str

class HolidayListResponse(BaseModel):
    success: bool
    data: List[HolidayItem]

class HolidayResponse(BaseModel):
    success: bool
    message: str
    data: Optional[HolidayItem] = None
