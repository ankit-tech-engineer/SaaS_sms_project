from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.core.dependencies import get_current_student_user
from app.modules.students.student_auth.schema import (
    StudentLoginRequest, StudentLoginResponse, StudentProfileResponse,
    ChangePasswordRequest, GenericResponse
)
from app.modules.students.student_auth.service import StudentAuthService

router = APIRouter(prefix="/auth")

@router.post("/login", response_model=StudentLoginResponse)
async def login(request: StudentLoginRequest):
    """
    Student Login.
    Returns Access & Refresh Tokens.
    """
    result = await StudentAuthService.login(request)
    return {
        "success": True,
        "data": result
    }

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 Compatible Token Endpoint (Form Data).
    Used by Swagger UI.
    Returns flat JSON: { access_token, token_type, ... }
    """
    # Map Form Data to Schema
    request = StudentLoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    result = await StudentAuthService.login(request)
    
    # Swagger/OAuth2 expects flat response with "token_type"
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "refresh_token": result["refresh_token"],
        "expires_in": result["expires_in"]
    }

@router.get("/profile", response_model=StudentProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_student_user)
):
    """
    Get current logged-in student's profile.
    """
    # current_user includes 'student_details' thanks to dependency
    student = current_user["student_details"]
    academic = student["academic"]
    
    profile_data = {
        "student_id": student["_id"],
        "name": f"{student['personal']['first_name']} {student['personal']['last_name']}",
        "class": academic["class_id"], # Schema maps 'class' -> 'class_name'
        "section": academic["section_id"],
        "roll_no": academic["roll_no"],
        "academic_year": academic["academic_year"],
        "role": "STUDENT"
    }
    
    return {
        "success": True,
        "data": profile_data
    }

@router.post("/change-password", response_model=GenericResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_student_user)
):
    """
    Change Student Password.
    Required on first login if force_password_change is True.
    """
    await StudentAuthService.change_password(current_user["_id"], request)
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }
