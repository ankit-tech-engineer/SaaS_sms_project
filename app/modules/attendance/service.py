from datetime import datetime, date
from uuid import uuid4
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
        teacher_id: str,
        user_type: str = "TEACHER" # Or pass context if needed
    ):
        """
        Mark Attendance with Centralized Validation.
        """
        # 1. Fetch Policy (Full Config)
        policy = await SchoolSettings.get_attendance_policy(school_id)
        
        # 2. Resolve Academic Year
        academic_year = get_current_academic_year()
        
        # 3. Validate
        # This function handles Pre-conditions (Holiday, Future), Permissions, Policy Rules
        from app.modules.attendance.validation import validate_attendance_marking
        
        validation_result = await validate_attendance_marking(
            request=request,
            policy=policy,
            school_id=school_id,
            teacher_id=teacher_id,
            user_type=user_type, # We might need to fetch user role from DB if passed generic 'TEACHER'
            academic_year=academic_year
        )
        
        # 4. Check for Existing Record & Handle Upsert
        query = {
            "school_id": school_id,
            "class_id": request.class_id,
            "section_id": request.section_id,
            "subject_id": validation_result["subject_id"], 
            "academic_year": academic_year,
            "date": request.date
        }
        
        database = db.get_db()
        existing = await database[COLLECTION_NAME].find_one(query)
        
        if existing:
            # Check Lock Status
            if existing.get("locked", False):
                # If Locked, ONLY Coordinator can edit (Implicitly Policy Mode = COORDINATOR_ONLY)
                # Or if Subject Teacher mode, blocked?
                # Policy says: COORDINATOR_ONLY -> Auto-Approved (Locked).
                # Implementation: Coordinator IS the authority. So they can OVERWRITE their own locked record.
                
                # We need to re-verify if current user allows editing locked records.
                # In COORDINATOR_ONLY mode: User is Coordinator. OK.
                # In SUBJECT_TEACHER mode: If Locked (Approved), Teacher Cannot Edit.
                
                if policy.get("mode") == "SUBJECT_TEACHER":
                     raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Attendance is locked/approved and cannot be modified."
                    )
        
        # 5. Upsert Record (Merge Logic)
        # We need to merge existing records with new ones to support partial updates.
        
        final_records_map = {}
        
        # A. Load existing records into map
        if existing and "records" in existing:
            for r in existing["records"]:
                # Ensure student_id key exists
                if "student_id" in r:
                    final_records_map[r["student_id"]] = r
                    
        # B. Overwrite/Append new records
        for r in request.records:
            final_records_map[r.student_id] = r.model_dump()
            
        final_records_list = list(final_records_map.values())
        
        update_doc = {
            "$set": {
                "records": final_records_list,
                "marked_by": teacher_id,
                "status": validation_result["status"],
                "locked": validation_result["locked"],
                "org_id": org_id, # Ensure these are set on insert
                "created_at": existing.get("created_at") if existing else datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {
                "_id": f"stu_atd_{uuid4().hex[:12]}"
            }
        }
        
        # Reset review if re-submitted in Subject Teacher mode?
        # If unlocked, yes.
        if not validation_result["locked"]:
            update_doc["$set"]["review"] = {
                "reviewed_by": None,
                "reviewed_at": None,
                "remarks": None
            }
            
        result = await database[COLLECTION_NAME].update_one(query, update_doc, upsert=True)
        
        # Return merged/updated doc
        doc = request.model_dump()
        doc.update({
            "_id": str(existing["_id"]) if existing else str(result.upserted_id),
            "status": validation_result["status"],
            "locked": validation_result["locked"]
        })
        return doc
        

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
