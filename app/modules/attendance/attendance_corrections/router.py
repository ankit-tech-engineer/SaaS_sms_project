from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.dependencies import get_current_teacher_user, get_current_school_user
from app.modules.attendance.attendance_corrections.schema import (
    CreateCorrectionRequest, 
    CorrectionResponse, 
    CoordinatorReviewRequest, 
    AdminReviewRequest
)
from app.modules.attendance.attendance_corrections.service import AttendanceCorrectionService
from app.utils.response import APIResponse

# Split Routers
teacher_router = APIRouter(
    prefix="/attendance/corrections"
)

admin_router = APIRouter(
    prefix="/attendance/corrections"
)

# --- TEACHER / COORDINATOR ROUTES ---

# 1. Raise Correction Request
@teacher_router.post("", status_code=status.HTTP_201_CREATED)
async def raise_correction_request(
    request: CreateCorrectionRequest,
    current_user: dict = Depends(get_current_teacher_user)
):
    teacher_id = current_user.get("teacher_id") or current_user.get("_id")
    school_id = current_user.get("school_id")
    org_id = current_user.get("org_id") 
    
    result = await AttendanceCorrectionService.raise_request(
        request=request,
        org_id=org_id, 
        school_id=school_id,
        user=current_user,
        user_role="TEACHER" 
    )
    return APIResponse.success(data=result, message="Correction request raised successfully")

# 2. Coordinator Review
@teacher_router.post("/{correction_id}/coordinator-review")
async def coordinator_review(
    correction_id: str,
    request: CoordinatorReviewRequest,
    current_user: dict = Depends(get_current_teacher_user)
):
    teacher_id = current_user.get("teacher_id") 
    school_id = current_user.get("school_id")
    
    result = await AttendanceCorrectionService.coordinator_review(
        correction_id=correction_id,
        action=request.action,
        remark=request.remark,
        school_id=school_id,
        coordinator_id=teacher_id
    )
    return APIResponse.success(data=result, message="Review submitted successfully")

# 3. Get Pending Requests (My Scope)
@teacher_router.get("/pending")
async def get_pending_requests(
    current_user: dict = Depends(get_current_teacher_user)
):
    school_id = current_user.get("school_id")
    
    teacher_details = current_user.get("teacher_details", {})
    is_coordinator = teacher_details.get("is_section_coordinator") or current_user.get("is_section_coordinator")
    role = "SECTION_COORDINATOR" if is_coordinator else "TEACHER"

    result = await AttendanceCorrectionService.get_pending_requests(
        school_id=school_id,
        user=current_user,
        user_role=role
    )
    return APIResponse.success(data=result, message="Pending requests fetched successfully") 


# --- ADMIN ROUTES ---

# 1. Admin Review & Apply
@admin_router.post("/{correction_id}/admin-review")
async def admin_review(
    correction_id: str,
    request: AdminReviewRequest,
    current_user: dict = Depends(get_current_school_user)
):
    # School Admin User
    user_id = current_user.get("_id")
    school_id = current_user.get("school_id")
    
    result = await AttendanceCorrectionService.admin_review(
        correction_id=correction_id,
        action=request.action,
        remark=request.remark,
        school_id=school_id,
        admin_id=user_id
    )
    return APIResponse.success(data=result, message="Review submitted successfully")

# 2. Get All Requests (Admin)
@admin_router.get("")
async def get_all_corrections(
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user.get("school_id")
    
    result = await AttendanceCorrectionService.get_all_requests(school_id=school_id)
    return APIResponse.success(data=result)
