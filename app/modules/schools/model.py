from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid

class SchoolAddress(BaseModel):
    line1: str
    city: str
    state: str
    country: str = "India"
    pincode: Optional[str] = None

class SchoolContact(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class SchoolBranding(BaseModel):
    logo_url: Optional[str] = None
    theme_color: str = "#1E40AF"

class SchoolSettings(BaseModel):
    academic_year: str = "2025-26"
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    language: str = "en"

class SchoolStats(BaseModel):
    students_count: int = 0
    teachers_count: int = 0
    classes_count: int = 0

class School(BaseModel):
    id: str = Field(default_factory=lambda: f"school_{uuid.uuid4().hex[:8]}", alias="_id")
    org_id: str
    school_name: str
    school_code: str
    
    contact: SchoolContact = Field(default_factory=SchoolContact)
    address: SchoolAddress
    branding: SchoolBranding = Field(default_factory=SchoolBranding)
    settings: SchoolSettings = Field(default_factory=SchoolSettings)
    stats: SchoolStats = Field(default_factory=SchoolStats)
    
    status: str = "active" # active | suspended | archived
    is_default: bool = False
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
