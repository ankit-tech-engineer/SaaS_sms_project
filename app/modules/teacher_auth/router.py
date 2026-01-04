from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.core.dependencies import get_current_teacher_user
from app.core.database import get_database
from app.modules.teacher_auth.schema import (
    TeacherLoginRequest, TeacherLoginResponse, TeacherProfileResponse,
    ChangePasswordRequest, GenericResponse
)
from app.modules.teacher_auth.service import TeacherAuthService

router = APIRouter(prefix="/auth")

@router.post("/login", response_model=TeacherLoginResponse)
async def login(request: TeacherLoginRequest):
    """
    Teacher Login (JSON).
    """
    result = await TeacherAuthService.login(request)
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
    request = TeacherLoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    result = await TeacherAuthService.login(request)
    
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "refresh_token": result["refresh_token"],
        "expires_in": result["expires_in"]
    }

@router.get("/profile", response_model=TeacherProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_teacher_user)
):
    """
    Get current logged-in teacher's profile.
    """
    teacher = current_user["teacher_details"]
    
    # Check coordinator status again or rely on token?
    # Token has it, but DB is fresher. Let's check DB for profile view to be accurate.
    # Actually, let's reuse the check logic or trust the token for speed? 
    # For profile view, fresh is better.
    
    db = await get_database()
    coordinator_record = await db["section_coordinators"].find_one({
        "teacher_id": teacher["_id"],
        "status": "active"
    })
    is_coord = True if coordinator_record else False
    
    profile_data = {
        "teacher_id": teacher["_id"],
        "name": f"{teacher['personal']['first_name']} {teacher['personal']['last_name']}",
        "is_section_coordinator": is_coord,
        "role": "TEACHER"
    }
    
    return {
        "success": True,
        "data": profile_data
    }

@router.post("/change-password", response_model=GenericResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_teacher_user)
):
    """
    Change Teacher Password.
    """
    await TeacherAuthService.change_password(current_user["_id"], request)
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }
