from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.core.database import db
from app.core.school_settings import SchoolSettings
from app.core.audit_logger import AuditLogger
from app.modules.attendance.model import COLLECTION_NAME as ATTENDANCE_COLLECTION
from app.modules.attendance_corrections.model import AttendanceCorrectionModel, COLLECTION_NAME as CORRECTION_COLLECTION
from app.modules.attendance_corrections.schema import CreateCorrectionRequest, ReviewDetails, CorrectionUser
from app.core.permissions import is_section_coordinator 

class AttendanceCorrectionService:
    
    @staticmethod
    async def raise_request(
        request: CreateCorrectionRequest,
        org_id: str,
        school_id: str,
        user: dict,
        user_role: str
    ):
        database = db.get_db()

        # 1. Global Validations
        # A. Check Org/School Status (Handled by Dependencies usually, but double check if needed)
        # B. Check Window
        policy = await SchoolSettings.get_attendance_policy(school_id)
        window_days = policy.get("attendance_correction_window_days", 3)
        
        # Fetch Attendance Record
        attendance = await database[ATTENDANCE_COLLECTION].find_one({
            "_id": request.attendance_id,
            "school_id": school_id
        })
        
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
            
        # Verify Date Window
        att_date = datetime.strptime(attendance["date"], "%Y-%m-%d").date() # Assuming date stored as YYYY-MM-DD
        today = datetime.utcnow().date()
        if (today - att_date).days > window_days:
             raise HTTPException(status_code=400, detail="Correction window has passed.")
             
        # Verify Status & Locked
        if attendance.get("status") != "APPROVED" or not attendance.get("locked"):
             raise HTTPException(status_code=400, detail="Correction can only be requested for APPROVED and LOCKED attendance.")

        # Find student record inside attendance
        student_record = next((r for r in attendance["records"] if r["student_id"] == request.student_id), None)
        if not student_record:
             raise HTTPException(status_code=404, detail="Student not found in this attendance record.")
             
        if student_record["status"] == request.requested_status:
             raise HTTPException(status_code=400, detail="Requested status is same as current status.")

        # Check for Duplicate Open Request
        existing_req = await database[CORRECTION_COLLECTION].find_one({
            "attendance_id": request.attendance_id,
            "student_id": request.student_id,
            "status": {"$in": ["REQUESTED", "COORDINATOR_APPROVED"]}
        })
        
        if existing_req:
             raise HTTPException(status_code=400, detail="A pending correction request already exists for this student.")

        # Role Check & Promotion
        # If the user is the Section Coordinator for this attendance's section, promote role to SECTION_COORDINATOR
        # This allows auto-approval logic to kick in.
        
        # We need to check if user["_id"] (or teacher_id) is coordinator for attendance["section_id"]
        # using the helper `is_section_coordinator`.
        teacher_id = user.get("teacher_id") or user.get("_id")
        if await is_section_coordinator(teacher_id, attendance["section_id"], school_id):
            user_role = "SECTION_COORDINATOR"

        # 2. Create Request Object
        initial_status = "REQUESTED"
        review_data = {
            "coordinator_id": None, 
            "coordinator_remark": None, 
            "admin_id": None, 
            "admin_remark": None
        }

        # Optimization: If Coordinator raises request, auto-approve to next stage
        if user_role == "SECTION_COORDINATOR":
            initial_status = "COORDINATOR_APPROVED"
            review_data["coordinator_id"] = user["_id"]
            review_data["coordinator_remark"] = "Auto-approved (Raised by Coordinator)"
            review_data["coordinator_reviewed_at"] = datetime.utcnow()

        correction_doc = request.model_dump()
        correction_doc.update({
            "org_id": org_id,
            "school_id": school_id,
            "attendance_date": attendance.get("date"), # Store as str or date object? Spec says "2025-08-10"
            "academic_year": attendance.get("academic_year"),
            "old_status": student_record["status"],
            "requested_by": {
                "user_id": user["_id"],
                "role": user_role
            },
            "review": review_data,
            "status": initial_status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            
            # Helper Fields for Querying
            "class_id": attendance.get("class_id"),
            "section_id": attendance.get("section_id")
        })
        
        return await AttendanceCorrectionModel.create_request(correction_doc)

    @staticmethod
    async def coordinator_review(
        correction_id: str,
        action: str,
        remark: str,
        school_id: str,
        coordinator_id: str
    ):
        database = db.get_db()
        
        # Fetch Correction
        correction = await AttendanceCorrectionModel.get_by_id(correction_id, school_id)
        if not correction:
            raise HTTPException(status_code=404, detail="Correction request not found")
            
        if correction["status"] != "REQUESTED":
            raise HTTPException(status_code=400, detail="Request is not in pending state.")
            
        # Verify Coordinator Permission (Must match section)
        # We stored section_id in correction doc for this purpose
        if not await is_section_coordinator(coordinator_id, correction["section_id"], school_id):
             raise HTTPException(status_code=403, detail="Not authorized to review corrections for this section.")

        new_status = "COORDINATOR_APPROVED" if action == "APPROVE" else "REJECTED"
        
        updates = {
            "status": new_status,
            "updated_at": datetime.utcnow(),
            "review.coordinator_id": coordinator_id,
            "review.coordinator_remark": remark,
            "review.coordinator_reviewed_at": datetime.utcnow()
        }
        
        await AttendanceCorrectionModel.update_status(correction_id, updates)
        correction.update(updates) # For return
        return correction

    @staticmethod
    async def admin_review(
        correction_id: str,
        action: str,
        remark: str,
        school_id: str,
        admin_id: str
    ):
        database = db.get_db()
        correction = await AttendanceCorrectionModel.get_by_id(correction_id, school_id)
        
        if not correction:
            raise HTTPException(status_code=404, detail="Correction request not found")
            
        # Admin can technically review any state, but workflow says after Coordinator.
        # But if Coordinator missed it, can Admin override? 
        # Strict workflow: Must be COORDINATOR_APPROVED.
        if correction["status"] != "COORDINATOR_APPROVED":
             # Optional: Allow skipping coordinator if needed, but spec says hierarchical.
             # Strict check:
             raise HTTPException(status_code=400, detail="Request must be approved by coordinator first.")
        
        if action == "REJECT":
            updates = {
                "status": "REJECTED",
                "updated_at": datetime.utcnow(),
                "review.admin_id": admin_id,
                "review.admin_remark": remark,
                "review.admin_reviewed_at": datetime.utcnow()
            }
            await AttendanceCorrectionModel.update_status(correction_id, updates)
            correction.update(updates)
            return correction
            
        elif action == "APPROVE":
            # CRITICAL: Apply Correction
            
            # 1. Update Attendance Collection
            # Find the specific element in array to update
            
            filter_query = {
                "_id": correction["attendance_id"],
                "records.student_id": correction["student_id"]
            }
            
            update_query = {
                "$set": {
                    "records.$.status": correction["requested_status"],
                    "records.$.corrected": True,
                    "records.$.correction_id": correction_id,
                    "records.$.correction_reason": correction["reason"] # Optional but good
                }
            }
            
            res = await database[ATTENDANCE_COLLECTION].update_one(filter_query, update_query)
            
            if res.modified_count == 0:
                 raise HTTPException(status_code=500, detail="Failed to apply correction to attendance record.")
            
            # 2. Update Correction Status
            updates = {
                "status": "ADMIN_APPROVED",
                "updated_at": datetime.utcnow(),
                "review.admin_id": admin_id,
                "review.admin_remark": remark,
                "review.admin_reviewed_at": datetime.utcnow()
            }
            await AttendanceCorrectionModel.update_status(correction_id, updates)
            
            # 3. Audit Log
            await AuditLogger.log_event(
                entity="attendance",
                entity_id=correction["attendance_id"],
                action="CORRECTION_APPLIED",
                old_value=correction["old_status"],
                new_value=correction["requested_status"],
                performed_by=admin_id,
                reason=f"Correction ID: {correction_id}. Admin Remark: {remark}"
            )
            
            correction.update(updates)
            return correction

    @staticmethod
    async def get_pending_requests(
        school_id: str,
        user: dict,
        user_role: str
    ):
        database = db.get_db()
        user_id = user.get("teacher_id") or user.get("_id")
        
        # Determine strict role for filtering
        # We need to pass section_ids for Coordinator to filter correctly.
        section_ids = None
        if user_role == "SECTION_COORDINATOR":
             # Optimization: Fetch coordinator's sections if possible.
             # For now, we trust the model to handle "all stats=REQUESTED" or we implement section filtering later if needed.
             pass
             
        return await AttendanceCorrectionModel.get_pending_requests(
            school_id=school_id,
            role=user_role,
            user_id=user_id,
            section_ids=section_ids
        )

    @staticmethod
    async def get_all_requests(school_id: str):
        return await AttendanceCorrectionModel.get_all_requests(school_id)
