from datetime import datetime
from typing import Literal
from uuid import uuid4
from fastapi import HTTPException
from app.core.database import get_database
from app.modules.teachers.teacher_assignments.model import TeacherAssignment
from app.modules.teachers.teacher_assignments.schema import CreateAssignmentRequest

class TeacherAssignmentService:
    @staticmethod
    async def assign_teacher(
        request: CreateAssignmentRequest,
        org_id: str,
        school_id: str,
        created_by: str
    ):
        db = await get_database()
        
        # 1. Validation: Teacher Exists & Active
        teacher = await db["teachers"].find_one({"_id": request.teacher_id, "school_id": school_id, "status": "active"})
        if not teacher:
            raise HTTPException(status_code=400, detail="Invalid or inactive teacher")
            
        # 2. Validation: Class & Section Exist
        class_doc = await db["classes"].find_one({"_id": request.class_id, "school_id": school_id})
        if not class_doc:
            raise HTTPException(status_code=400, detail="Invalid class")

        section_doc = await db["sections"].find_one({"_id": request.section_id, "class_id": request.class_id, "school_id": school_id})
        if not section_doc:
            raise HTTPException(status_code=400, detail="Invalid section or section does not belong to the specified class")
        
        subject = await db["subjects"].find_one({"_id": request.subject_id, "class_id": request.class_id, "school_id": school_id})
        if not subject:
             raise HTTPException(status_code=400, detail="Invalid subject or subject does not belong to the specified class")
             
        # 3. Role-Based Logic Check
        
        # Check Existing Primary
        existing_primary = await db["teacher_assignments"].find_one({
            "school_id": school_id,
            "class_id": request.class_id,
            "section_id": request.section_id,
            "subject_id": request.subject_id,
            "academic_year": request.academic_year,
            "role_type": "PRIMARY", # Use literal
            "status": "active"
        })

        if request.role_type == "PRIMARY":
            if existing_primary:
                # If trying to assign PRIMARY, but one already exists -> ERROR
                 raise HTTPException(status_code=400, detail="A PRIMARY teacher is already assigned to this subject. Please unassign them first.")
        else:
            # If CO_TEACHER or SUBSTITUTE -> PRIMARY must exist
            if not existing_primary:
                raise HTTPException(status_code=400, detail=f"Cannot assign {request.role_type} without an active PRIMARY teacher.")
        
        # 4. Duplicate Check (Teacher-specific)
        duplicate = await db["teacher_assignments"].find_one({
            "teacher_id": request.teacher_id,
            "class_id": request.class_id,
            "section_id": request.section_id,
            "subject_id": request.subject_id,
            "academic_year": request.academic_year,
            "status": "active"
        })
        
        if duplicate:
             raise HTTPException(status_code=400, detail=f"Teacher is already assigned as {duplicate.get('role_type')} to this subject.")

        # 5. Create Assignment
        assign_id = f"assign_{uuid4().hex[:12]}"
        
        substitute_period = None
        if request.role_type == "SUBSTITUTE":
            substitute_period = {
                "from": request.substitute_from.isoformat(),
                "to": request.substitute_to.isoformat()
            }

        assignment = TeacherAssignment(
            _id=assign_id,
            org_id=org_id,
            school_id=school_id,
            teacher_id=request.teacher_id,
            class_id=request.class_id,
            section_id=request.section_id,
            subject_id=request.subject_id,
            academic_year=request.academic_year,
            role_type=request.role_type,
            substitute_period=substitute_period,
            status="active",
            assigned_by=created_by
        )
        
        await db["teacher_assignments"].insert_one(assignment.model_dump(by_alias=True))
        
        # Fetch Class and Section details for response
        class_doc = await db["classes"].find_one({"_id": request.class_id})
        section_doc = await db["sections"].find_one({"_id": request.section_id})

        return {
            "success": True,
            "message": "Teacher assigned successfully",
            "data": {
                "assignment_id": assign_id,
                "teacher_name": f"{teacher['personal']['first_name']} {teacher['personal']['last_name']}",
                "subject_name": subject["subject_name"],
                "class_name": class_doc["class_name"] if class_doc else "Unknown Class",
                "section_name": section_doc["section_name"] if section_doc else "Unknown Section",
                "role_type": request.role_type,
                "academic_year": request.academic_year,
                "assigned_at": datetime.utcnow()
            }
        }


    @staticmethod
    async def unassign_teacher(
        assignment_id: str,
        school_id: str
    ):
        db = await get_database()
        result = await db["teacher_assignments"].update_one(
            {"_id": assignment_id, "school_id": school_id, "status": "active"},
            {"$set": {"status": "inactive"}}
        )
        
        if result.modified_count == 0:
             raise HTTPException(status_code=404, detail="Assignment not found or already inactive")
             
        return {"success": True, "message": "Teacher unassigned successfully"}

    @staticmethod
    async def list_assignments(
        school_id: str,
        class_id: str = None,
        section_id: str = None,
        teacher_id: str = None
    ):
        db = await get_database()
        query = {"school_id": school_id, "status": "active"}
        
        if class_id: query["class_id"] = class_id
        if section_id: query["section_id"] = section_id
        if teacher_id: query["teacher_id"] = teacher_id
        
        pipeline = [
            {"$match": query},
            # Join Teacher
            {"$lookup": {
                "from": "teachers",
                "localField": "teacher_id",
                "foreignField": "_id",
                "as": "teacher"
            }},
            {"$unwind": "$teacher"},
            # Join Subject
            {"$lookup": {
                "from": "subjects",
                "localField": "subject_id",
                "foreignField": "_id",
                "as": "subject"
            }},
            {"$unwind": "$subject"},
            # Join Class
            {"$lookup": {
                "from": "classes",
                "localField": "class_id",
                "foreignField": "_id",
                "as": "class"
            }},
            {"$unwind": "$class"},
            # Join Section
            {"$lookup": {
                "from": "sections",
                "localField": "section_id",
                "foreignField": "_id",
                "as": "section"
            }},
            {"$unwind": "$section"},
            
            {"$project": {
                "assignment_id": "$_id",
                "teacher_name": {"$concat": ["$teacher.personal.first_name", " ", "$teacher.personal.last_name"]},
                "subject_name": "$subject.subject_name",
                "class_name": "$class.class_name",
                "section_name": "$section.section_name",
                "role_type": "$role_type",
                "academic_year": "$academic_year",
                "assigned_at": "$assigned_at"
            }}
        ]
        
        return await db["teacher_assignments"].aggregate(pipeline).to_list(length=1000)

    @staticmethod
    async def check_teacher_permission(
        teacher_id: str,
        class_id: str,
        section_id: str,
        subject_id: str,
        action: Literal["ATTENDANCE", "MARKS", "ASSIGNMENT"]
    ) -> bool:
        """
        Check if a teacher has active assignment for context and role permissions.
        """
        db = await get_database()
        assignment = await db["teacher_assignments"].find_one({
            "teacher_id": teacher_id,
            "class_id": class_id,
            "section_id": section_id,
            "subject_id": subject_id,
            "status": "active"
        })
        
        if not assignment:
            return False
            
        role = assignment.get("role_type", "PRIMARY") # Default to Primary if missing
        
        # 1. PRIMARY: Can do everything
        if role == "PRIMARY":
            return True
            
        # 2. CO_TEACHER: Can create assignments (optional), but NO Attendance/Marks
        if role == "CO_TEACHER":
            if action == "ASSIGNMENT":
                return True
            return False # No Attendance, No Marks
            
        # 3. SUBSTITUTE: Only Attendance, Only within date range
        if role == "SUBSTITUTE":
            if action != "ATTENDANCE":
                return False
                
            # Check Date Range
            sub_period = assignment.get("substitute_period", {})
            if not sub_period: return False
            
            start_str = sub_period.get("from")
            end_str = sub_period.get("to")
            
            if not start_str or not end_str: return False
            
            today = datetime.utcnow().date()
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            
            if start_date <= today <= end_date:
                return True
            
            return False

        return False
