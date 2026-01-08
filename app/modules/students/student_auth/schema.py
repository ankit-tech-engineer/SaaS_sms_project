from typing import Optional
from pydantic import BaseModel, Field

class StudentLoginRequest(BaseModel):
    username: str
    password: str

class TokenResponseData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    force_password_change: bool

class StudentLoginResponse(BaseModel):
    success: bool
    data: TokenResponseData

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    
class GenericResponse(BaseModel):
    success: bool
    message: str

class StudentProfileData(BaseModel):
    student_id: str
    name: str
    class_name: str = Field(..., alias="class") # 'class' is reserved keyword
    section: str
    roll_no: int
    academic_year: str
    role: str = "STUDENT"
    
    class Config:
        populate_by_name = True

class StudentProfileResponse(BaseModel):
    success: bool
    data: StudentProfileData
