from datetime import datetime, date
from typing import Optional, Union
from pydantic import BaseModel, Field, EmailStr

class PersonalInfo(BaseModel):
    first_name: str
    last_name: str
    gender: str
    dob: Union[datetime, str] # MongoDB requires datetime

class ContactInfo(BaseModel):
    mobile: str
    email: EmailStr

class ProfessionalInfo(BaseModel):
    qualification: str
    experience_years: int
    joining_date: Optional[datetime] = None

class Teacher(BaseModel):
    id: str = Field(alias="_id")
    org_id: str
    school_id: str
    
    personal: PersonalInfo
    contact: ContactInfo
    professional: ProfessionalInfo
    
    status: str = "active"
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
