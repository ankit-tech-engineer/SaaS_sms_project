from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field

# Request Sub-Schemas
class AcademicRequest(BaseModel):
    class_id: str
    section_id: str
    admission_no: str

class PersonalRequest(BaseModel):
    first_name: str
    last_name: str
    gender: str
    dob: date

class ParentRequest(BaseModel):
    father_name: str
    mother_name: str
    mobile: str
    email: Optional[EmailStr] = None

# Request Schema
class StudentAdmissionRequest(BaseModel):
    academic: AcademicRequest
    personal: PersonalRequest
    parent: ParentRequest


# Response Sub-Schemas
class AcademicResponse(BaseModel):
    roll_no: int
    academic_year: str

class StudentLoginResponse(BaseModel):
    username: str
    temporary_password: str

class StudentAdmissionResponseData(BaseModel):
    student_id: str
    academic: AcademicResponse
    student_login: StudentLoginResponse

class StudentAdmissionResponse(BaseModel):
    success: bool
    message: str
    data: StudentAdmissionResponseData
