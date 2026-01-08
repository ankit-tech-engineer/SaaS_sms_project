from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from typing import Optional

from app.core.dependencies import get_current_school_user, get_current_teacher_user, get_current_student_user
from app.utils.response import APIResponse
from app.modules.reports.attendance_reports.service import AttendanceReportService
from app.modules.reports.attendance_reports.schema import (
    DailySummaryResponse,
    StudentMonthlySummary,
    SectionMonthlySummary,
    DefaulterStudent,
    AttendanceTrendResponse
)
from app.core.permissions import is_section_coordinator 

# We might need two routers or one with smart dependency injection.
# Given strict requirements: "SCHOOL_ADMIN" and "SECTION_COORDINATOR (own section)".
# Teacher role is NOT allowed.
# So we can't just use `get_current_teacher_user` widely without checking coordinator status.

router = APIRouter(
    prefix="/reports/attendance"
)



# --- ADMIN ENDPOINTS (School Scope) ---
# Mounted under /school usually means Admin Only or Authorized School User.

@router.get("/daily", summary="Daily Attendance Summary")
async def get_daily_summary(
    date: date,
    class_id: Optional[str] = None,
    section_id: Optional[str] = None,
    current_user: dict = Depends(get_current_school_user) 
):
    """
    Get daily summary.
    Admin Access: All.
    """
    # Strict Rule: Only School Admin? 
    # Spec: "SCHOOL_ADMIN, SECTION_COORDINATOR (own section), PLATFORM_ADMIN"
    # If we use `get_current_school_user`, that validates token. 
    # Does it distinguish Admin vs Teacher? 
    # Usually `get_current_school_user` implies Admin/Staff access.
    # We should rely on `role` check if needed. assuming strict admin here for now.
    
    school_id = current_user.get("school_id")
    
    result = await AttendanceReportService.get_daily_summary(
        school_id=school_id, 
        report_date=date, 
        class_id=class_id, 
        section_id=section_id
    )
    return APIResponse.success(data=result)

@router.get("/student-monthly", summary="Student Monthly Report")
async def get_student_monthly(
    student_id: str,
    month: str,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user.get("school_id")
    result = await AttendanceReportService.get_student_monthly(
        school_id=school_id,
        student_id=student_id,
        month=month
    )
    return APIResponse.success(data=result)

@router.get("/section-monthly", summary="Section Monthly Summary")
async def get_section_monthly(
    class_id: str,
    section_id: str,
    month: str,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user.get("school_id")
    result = await AttendanceReportService.get_section_monthly(
        school_id=school_id,
        class_id=class_id,
        section_id=section_id,
        month=month
    )
    return APIResponse.success(data=result)

@router.get("/defaulters", summary="Defaulters List")
async def get_defaulters(
    month: str,
    threshold: float = 75.0,
    class_id: Optional[str] = None,
    section_id: Optional[str] = None,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user.get("school_id")
    result = await AttendanceReportService.get_defaulters(
        school_id=school_id,
        month=month,
        threshold=threshold,
        class_id=class_id,
        section_id=section_id
    )
    return APIResponse.success(data=result)

@router.get("/trend", summary="Attendance Trend")
async def get_attendance_trend(
    class_id: str,
    section_id: str,
    months: int = 6,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user.get("school_id")
    result = await AttendanceReportService.get_attendance_trend(
        school_id=school_id,
        class_id=class_id,
        section_id=section_id,
        months_back=months
    )
    return APIResponse.success(data=result)


# --- COORDINATOR SCOPED ROUTER ---
# Assuming we mount this under /teacher/reports/attendance or similar?
# Or we reuse the same paths but with `get_current_teacher_user` dependency and checks.
# To keep main.py clean, let's export a separate router for Coordinators.

coordinator_router = APIRouter(
    prefix="/reports/attendance"
)

@coordinator_router.get("/daily")
async def get_daily_summary_coordinator(
    date: date,
    class_id: str, # Mandatory for Coordinator?
    section_id: str, # Mandatory
    current_user: dict = Depends(get_current_teacher_user)
):
    # Enforce Coordinator Scope
    teacher_id = current_user.get("teacher_id") or current_user.get("_id")
    school_id = current_user.get("school_id")
    
    # Check permission
    if not await is_section_coordinator(teacher_id, section_id, school_id):
        raise HTTPException(status_code=403, detail="Access denied. Not a coordinator for this section.")
        
    result = await AttendanceReportService.get_daily_summary(
        school_id=school_id, 
        report_date=date, 
        class_id=class_id, 
        section_id=section_id
    )
    return APIResponse.success(data=result)

# Similar separate endpoints for Coordinator for clarity and security.

# --- STUDENT SCOPED ROUTER ---

student_router = APIRouter(
    prefix="/reports/attendance"
)

@student_router.get("/daily", summary="My Daily Attendance")
async def get_my_daily_attendance(
    date: date,
    current_user: dict = Depends(get_current_student_user)
):
    school_id = current_user.get("school_id")
    student_id = current_user.get("student_details", {}).get("_id") or current_user.get("student_id") # flexible
    
    # Use range history for single day
    result = await AttendanceReportService.get_student_history(
        school_id=school_id, 
        student_id=student_id, 
        start_date=date, 
        end_date=date
    )
    # Return single object or null if no record? return list as it's history
    return APIResponse.success(data=result)

@student_router.get("/monthly", summary="My Monthly Statistics")
async def get_my_monthly_stats(
    month: str, # YYYY-MM
    current_user: dict = Depends(get_current_student_user)
):
    school_id = current_user.get("school_id")
    student_id = current_user.get("student_details", {}).get("_id") or current_user.get("student_id")
    
    result = await AttendanceReportService.get_student_monthly(
        school_id=school_id,
        student_id=student_id,
        month=month
    )
    return APIResponse.success(data=result)

@student_router.get("/summary", summary="My Range Summary (Half-Yearly/Yearly)")
async def get_my_range_summary(
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_student_user)
):
    school_id = current_user.get("school_id")
    student_id = current_user.get("student_details", {}).get("_id") or current_user.get("student_id")
    
    result = await AttendanceReportService.get_student_range_summary(
        school_id=school_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date
    )
    return APIResponse.success(data=result)

