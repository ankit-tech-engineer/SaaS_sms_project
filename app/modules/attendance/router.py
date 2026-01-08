from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_teacher_user, get_current_school_user
from app.core.school_settings import SchoolSettings
from app.modules.attendance.schema import (
    MarkAttendanceRequest, ReviewAttendanceRequest, GenericAttendanceResponse,
    SetPolicyRequest, PolicyResponse
)
from app.modules.attendance.service import AttendanceService

router = APIRouter()

@router.post("/set-attendance-policy", response_model=PolicyResponse)
async def set_attendance_policy(
    request: SetPolicyRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Set School Attendance Policy (School Admin Only).
    """
    if current_user["role"] != "SCHOOL_ADMIN":
         raise HTTPException(
            status_code=403, 
            detail="Only School Admin can configure attendance policy."
        )
        
    await SchoolSettings.set_attendance_policy(
        school_id=current_user["school_id"],
        mode=request.mode,
        past_attendance_days_allowed=request.past_attendance_days_allowed
    )
    
    return {
        "success": True,
        "mode": request.mode,
        "past_attendance_days_allowed": request.past_attendance_days_allowed
    }

@router.get("/get-attendance-policy", response_model=PolicyResponse)
async def get_attendance_policy(
    current_user: dict = Depends(get_current_school_user)
):
    """
    Get School Attendance Policy.
    """
    policy = await SchoolSettings.get_attendance_policy(
        school_id=current_user["school_id"]
    )
    
    return {
        "success": True,
        "mode": policy["mode"],
        "past_attendance_days_allowed": policy["past_attendance_days_allowed"]
    }


@router.post("/student-attendance/mark", response_model=GenericAttendanceResponse)
async def mark_attendance(
    request: MarkAttendanceRequest,
    current_user: dict = Depends(get_current_teacher_user)
):
    """
    Mark Student Attendance.
    - Behavior depends on School Policy (COORDINATOR_ONLY vs SUBJECT_TEACHER).
    """
    result = await AttendanceService.mark_attendance(
        request=request,
        org_id=current_user["org_id"],
        school_id=current_user["school_id"],
        teacher_id=current_user["teacher_details"]["_id"]
    )
    
    return {
        "success": True,
        "message": "Attendance marked successfully",
        "data": result
    }

@router.post("/student-attendance/{attendance_id}/review", response_model=GenericAttendanceResponse)
async def review_attendance(
    attendance_id: str,
    request: ReviewAttendanceRequest,
    current_user: dict = Depends(get_current_teacher_user)
):
    """
    Review Attendance (Approve/Reject).
    - Only for Section Coordinators in SUBJECT_TEACHER mode.
    """
    result = await AttendanceService.review_attendance(
        attendance_id=attendance_id,
        request=request,
        teacher_id=current_user["teacher_details"]["_id"],
        school_id=current_user["school_id"]
    )
    
    return {
        "success": True,
        "message": f"Attendance {request.action.lower()}ed successfully",
        "data": result
    }

