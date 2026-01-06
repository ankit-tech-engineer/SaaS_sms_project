from datetime import datetime, date
from typing import Optional
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status

from app.core.database import db
from app.core.school_settings import SchoolSettings
from app.core.permissions import is_section_coordinator, validate_teacher_assignment
from app.modules.attendance.model import COLLECTION_NAME
from app.modules.attendance.schema import MarkAttendanceRequest, ReviewAttendanceRequest
from app.modules.holidays.service import HolidayService
from app.core.academic_year import get_current_academic_year

class AttendanceService:
    
    @staticmethod
    async def mark_attendance(
        request: MarkAttendanceRequest,
        org_id: str,
        school_id: str,
        teacher_id: str
    ):
        """
        Mark Attendance with Hybrid Logic.
        """
        # 1. Resolve Policy
        policy_mode = await SchoolSettings.get_attendance_policy(school_id)
        
        # 2. Check Holiday
        if await HolidayService.is_holiday(school_id, request.date):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendance cannot be marked on a holiday ({request.date})."
            )
            
        # 3. Resolve Academic Year
        academic_year = get_current_academic_year() # Assuming this is synchronous or we await if needed. Check import.
        # It's usually a function.
        
        # 4. Mode Specific Logic
        status_val = "SUBMITTED"
        locked = False
        final_subject_id = request.subject_id
        
        attendance_date = date.fromisoformat(request.date)

        if policy_mode == "COORDINATOR_ONLY":
            # Guard: Must be Coordinator
            if not await is_section_coordinator(teacher_id, request.section_id, school_id):
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Section Coordinators can mark attendance in this mode."
                )
            
            # Enforce Subject ID -> None
            final_subject_id = None
            status_val = "APPROVED"
            locked = True
            
        elif policy_mode == "SUBJECT_TEACHER":
            # Guard: Must be Assigned Teacher (Primary or Substitute)
            if not request.subject_id:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject ID is required in SUBJECT_TEACHER mode."
                )
                
            is_valid = await validate_teacher_assignment(
                teacher_id, request.class_id, request.section_id, request.subject_id, school_id, attendance_date
            )
            
            if not is_valid:
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to mark attendance for this subject/class."
                )
            
            status_val = "SUBMITTED"
            locked = False
            
        # 5. Insert Record
        doc = request.model_dump()
        doc.update({
            "org_id": org_id,
            "school_id": school_id,
            "subject_id": final_subject_id, # Overwrite with None if COORD mode
            "academic_year": academic_year,
            "marked_by": teacher_id,
            "status": status_val,
            "locked": locked,
            "created_at": datetime.utcnow(),
            "review": {
                "reviewed_by": None,
                "reviewed_at": None,
                "remarks": None
            }
        })
        
        database = db.get_db()
        try:
            result = await database[COLLECTION_NAME].insert_one(doc)
            doc["_id"] = str(result.inserted_id)
            return doc
        except DuplicateKeyError:
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already marked for this date/subject."
            )

    @staticmethod
    async def review_attendance(
        attendance_id: str,
        request: ReviewAttendanceRequest,
        teacher_id: str,
        school_id: str
    ):
        """
        Review Attendance (Approve/Reject) by Coordinator.
        """
        database = db.get_db()
        
        # 1. Fetch Attendance
        record = await database[COLLECTION_NAME].find_one({"_id": attendance_id, "school_id": school_id})
        if not record:
             raise HTTPException(status_code=404, detail="Attendance record not found")
        
        if record["locked"] and record["status"] == "APPROVED":
             raise HTTPException(status_code=400, detail="Attendance is already approved and locked.")
             
        # 2. Verify Coordinator Logic
        # Coordinator must match the section of the record
        if not await is_section_coordinator(teacher_id, record["section_id"], school_id):
             raise HTTPException(status_code=403, detail="Only the Section Coordinator can review this attendance.")
             
        # Guard: Teacher cannot approve own attendance?
        if record["marked_by"] == teacher_id:
             raise HTTPException(status_code=403, detail="You cannot approve your own attendance submission.")

        # 3. Apply Review
        update_data = {
            "status": "APPROVED" if request.action == "APPROVE" else "REJECTED",
            "locked": True if request.action == "APPROVE" else False,
            "review": {
                "reviewed_by": teacher_id,
                "reviewed_at": datetime.utcnow(),
                "remarks": request.remarks
            }
        }
        
        await database[COLLECTION_NAME].update_one(
            {"_id": attendance_id},
            {"$set": update_data}
        )
        
        record.update(update_data)
        record["_id"] = str(record["_id"])
        return record
