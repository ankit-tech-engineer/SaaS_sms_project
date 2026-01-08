from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# --- Login ---
class TeacherLoginRequest(BaseModel):
    username: str
    password: str

class TeacherLoginResponseData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    force_password_change: bool

class TeacherLoginResponse(BaseModel):
    success: bool
    data: TeacherLoginResponseData

# --- Profile ---
class TeacherProfileData(BaseModel):
    teacher_id: str
    name: str # Combined first + last
    is_section_coordinator: bool
    role: str = "TEACHER"

class TeacherProfileResponse(BaseModel):
    success: bool
    data: TeacherProfileData

# --- Change Password ---
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class GenericResponse(BaseModel):
    success: bool
    message: str
