from typing import Optional, Union
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr

class AcademicInfo(BaseModel):
    class_id: str
    section_id: str
    roll_no: int
    admission_no: str
    academic_year: str

class PersonalInfo(BaseModel):
    first_name: str
    last_name: str
    gender: str
    dob: Union[datetime, str]  # MongoDB requires datetime

class ParentInfo(BaseModel):
    father_name: str
    mother_name: str
    mobile: str
    email: Optional[EmailStr] = None

class Student(BaseModel):
    id: str = Field(alias="_id")
    org_id: str
    school_id: str
    academic: AcademicInfo
    personal: PersonalInfo
    parent: ParentInfo
    status: str = "active"
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
