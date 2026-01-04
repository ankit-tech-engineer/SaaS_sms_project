from typing import Optional, Union
from datetime import datetime, date
from pydantic import BaseModel, EmailStr

# --- Nested Requests ---
class PersonalRequest(BaseModel):
    first_name: str
    last_name: str
    gender: str
    dob: Union[date, str, datetime]

class ContactRequest(BaseModel):
    mobile: str
    email: EmailStr

class ProfessionalRequest(BaseModel):
    qualification: str
    experience_years: int
    joining_date: Optional[Union[date, str, datetime]] = None

# --- Main Create Request ---
class CreateTeacherRequest(BaseModel):
    personal: PersonalRequest
    contact: ContactRequest
    professional: ProfessionalRequest

# --- Response ---
class TeacherLoginCredentials(BaseModel):
    username: str
    temporary_password: str

class TeacherResponseData(BaseModel):
    teacher_id: str
    login: TeacherLoginCredentials

class CreateTeacherResponse(BaseModel):
    success: bool
    data: TeacherResponseData
