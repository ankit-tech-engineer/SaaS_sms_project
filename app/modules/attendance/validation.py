from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from fastapi import HTTPException, status
from app.core.database import db
from app.modules.attendance.schema import MarkAttendanceRequest
from app.core.permissions import is_section_coordinator, validate_teacher_assignment
from app.modules.holidays.service import HolidayService

async def validate_attendance_marking(
    request: MarkAttendanceRequest,
    policy: Dict[str, Any],
    school_id: str,
    teacher_id: str,
    user_type: str,
    academic_year: str
) -> Dict[str, Any]:
    """
    Central Logic to Validate Attendance Marking Rules.
    Returns: {"status": str, "locked": bool}
    Throws: HTTPException on any rule violation.
    """
    database = db.get_db()
    
    # --- 1. Global Pre-Conditions ---
    
    # Date Parsing
    try:
        attendance_date = date.fromisoformat(request.date)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid date format")

    today = date.today()
    
    # 1.1 Future Date Check
    if attendance_date > today:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "Cannot mark attendance for a future date"
        )
    
    # 1.2 Holiday Check 
    if await HolidayService.is_holiday(school_id, request.date):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            f"Cannot mark attendance on a holiday: {request.date}"
        )
        
    # 1.3 Validate Class/Section/Student Integrity
    # Extract student IDs
    student_ids = [r.student_id for r in request.records]
    if not student_ids:
         raise HTTPException(status.HTTP_400_BAD_REQUEST, "Records list cannot be empty")
         
    # Fetch students
    # Only fetch fields needed for validation
    students = await database["students"].find(
        {"_id": {"$in": student_ids}},
        {"_id": 1, "school_id": 1, "academic": 1, "status": 1}
    ).to_list(length=len(student_ids))
    
    if len(students) != len(set(student_ids)):
        # Identify missing
        found_ids = {s["_id"] for s in students}
        missing = set(student_ids) - found_ids
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Some student IDs are invalid or not found: {missing}"
        )
        
    # Validate Membership
    for student in students:
        if student.get("school_id") != school_id:
             raise HTTPException(status.HTTP_403_FORBIDDEN, f"Student {student['_id']} belongs to a different school.")
             
        if student.get("status") != "active":
             raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Student {student['_id']} is not active.")
             
        if student.get("academic").get("class_id") != request.class_id or student.get("academic").get("section_id") != request.section_id:
             raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                f"Student {student['_id']} does not belong to the specified Class ({request.class_id}) and Section ({request.section_id})."
            )

    # --- 2. Resolve Policy Mode ---
    mode = policy.get("mode", "COORDINATOR_ONLY")
    past_days_allowed = policy.get("past_attendance_days_allowed", 0)
    
    # --- 3. Mode Specific Logic ---
    
    if mode == "COORDINATOR_ONLY":
        # Rule 1: Must be Section Coordinator
        if not await is_section_coordinator(teacher_id, request.section_id, school_id):
             raise HTTPException(
                status.HTTP_403_FORBIDDEN, 
                "COORDINATOR_ONLY mode: You are not the coordinator for this section."
            )
        
        # Rule 2: Subject ID MUST be NULL 
        if request.subject_id:
             raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                "COORDINATOR_ONLY mode: Subject ID must be empty."
            )
            
        # Rule 3: Date Rules
        if attendance_date < today:
            delta = (today - attendance_date).days
            if delta > past_days_allowed:
                 raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, 
                    f"COORDINATOR_ONLY mode: Cannot mark attendance older than {past_days_allowed} days."
                )
        
        # Rule 4: Auto-Approved
        return {"status": "APPROVED", "locked": True, "subject_id": None}
        
    elif mode == "SUBJECT_TEACHER":
        # Rule 1: User MUST be Teacher
        if user_type != "TEACHER_USER" and user_type != "TEACHER": 
             pass 

        # Rule 2: Subject ID Required
        if not request.subject_id:
             raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                "SUBJECT_TEACHER mode: Subject ID is required."
            )
            
        # Rule 3: Valid Assignment
        is_assigned = await validate_teacher_assignment(
            teacher_id, request.class_id, request.section_id, request.subject_id, school_id, attendance_date
        )
        if not is_assigned:
             raise HTTPException(
                status.HTTP_403_FORBIDDEN, 
                "SUBJECT_TEACHER mode: You do not have a valid assignment for this class/subject/date."
            )
            
        # Rule 5: Date Rules (STRICT)
        # date != today -> Reject
        if attendance_date != today:
             raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                "SUBJECT_TEACHER mode: You can only mark attendance for TODAY."
            )
            
        # Rule 6: Not Final
        return {"status": "SUBMITTED", "locked": False, "subject_id": request.subject_id}
        
    else:
        # Fallback / Unknown Mode
         raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Unknown Attendance Policy Mode")
