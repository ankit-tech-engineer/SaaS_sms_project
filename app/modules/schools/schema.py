from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional, Dict, Any
from datetime import datetime

# Nested Schemas for Request
# Nested Schemas for Request
class AddressRequest(BaseModel):
    line1: str
    city: str
    state: str
    country: str = "India"
    pincode: Optional[str] = None

class ContactRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class SettingsRequest(BaseModel):
    academic_year: str = "2025-26"
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    language: str = "en"

class BrandingRequest(BaseModel):
    logo_url: Optional[str] = None
    theme_color: Optional[str] = None

# Create Request
class CreateSchoolRequest(BaseModel):
    school_name: str = Field(..., min_length=3, max_length=100)
    school_code: str = Field(..., min_length=3, max_length=20, pattern=r"^[A-Z0-9-]+$")
    
    contact: ContactRequest
    address: AddressRequest
    settings: Optional[SettingsRequest] = Field(default_factory=SettingsRequest)
    branding: Optional[BrandingRequest] = Field(default_factory=BrandingRequest)

# Update Request
class UpdateSchoolRequest(BaseModel):
    school_name: Optional[str] = None
    contact: Optional[ContactRequest] = None
    address: Optional[AddressRequest] = None
    branding: Optional[BrandingRequest] = None
    settings: Optional[SettingsRequest] = None

# Status Update
class SchoolStatusUpdate(BaseModel):
    status: str

    @field_validator('status')
    def validate_status(cls, v):
        if v not in ['active', 'suspended', 'archived']:
            raise ValueError('Invalid status')
        return v

# Response
class SchoolResponse(BaseModel):
    id: str = Field(alias="_id")
    org_id: str
    school_name: str
    school_code: str
    status: str
    is_default: bool
    address: Dict[str, Any]
    branding: Dict[str, Any]
    stats: Dict[str, int]
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)

# Auth Response for Auto-Created Admin
class CreateSchoolAdminResponse(BaseModel):
    email: EmailStr
    access_token: str
    password: str # Returned ONLY on creation
    expires_in: int

class SchoolCreationResponse(BaseModel):
    school_id: str
    school_admin: CreateSchoolAdminResponse
