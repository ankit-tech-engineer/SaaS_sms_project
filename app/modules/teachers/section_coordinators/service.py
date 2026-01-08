from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from app.core.database import get_database
from app.modules.teachers.section_coordinators.model import SectionCoordinator

class SectionCoordinatorService:
    @staticmethod
    async def assign_coordinator(
        section_id: str,
        teacher_id: str,
        org_id: str,
        school_id: str
    ):
        db = await get_database()
        
        # 1. Validate Teacher
        teacher = await db["teachers"].find_one({"_id": teacher_id, "school_id": school_id})
        if not teacher or teacher.get("status") != "active":
             raise HTTPException(status_code=400, detail="Invalid or inactive teacher")
             
        # 2. Validate Section
        section = await db["sections"].find_one({"_id": section_id, "school_id": school_id})
        if not section:
             raise HTTPException(status_code=400, detail="Invalid section")
             
        class_id = section.get("class_id")

        # 3. Rule: Teacher can coordinate ONLY ONE section
        # Check if teacher is already assigned to ANY active section
        existing_assignment = await db["section_coordinators"].find_one({
            "teacher_id": teacher_id,
            "status": "active"
        })
        if existing_assignment:
            # If assigned to THIS section, nothing to do (or error?)
            if existing_assignment["section_id"] == section_id:
                return {"message": "Teacher already assigned to this section"}
            else:
                # Decide: Error or reassignment?
                # User prompted: "A teacher can coordinate ONLY ONE section"
                # Let's enforce strictly. They must be removed first? 
                # Or auto-remove? Let's auto-remove (replace) logic or raise conflict.
                # Simplest for now: Raise conflict
                raise HTTPException(status_code=400, detail="Teacher is already a coordinator for another section")

        # 4. Rule: One section can have ONLY ONE coordinator
        # Remove existing coordinator for THIS section (if any)
        # We perform a logical delete (set status=inactive)
        await db["section_coordinators"].update_many(
            {"section_id": section_id, "status": "active"},
            {"$set": {"status": "inactive", "removed_at": datetime.utcnow()}}
        )
        
        # 5. Assign New Coordinator
        coord_id = f"coord_{uuid4().hex[:12]}"
        
        coord_doc = SectionCoordinator(
            _id=coord_id,
            org_id=org_id,
            school_id=school_id,
            teacher_id=teacher_id,
            class_id=class_id,
            section_id=section_id,
            status="active",
            assigned_at=datetime.utcnow()
        )
        
        await db["section_coordinators"].insert_one(coord_doc.model_dump(by_alias=True))
        
        return {
            "success": True,
            "message": "Coordinator assigned successfully",
            "data": {
                "coordinator_id": coord_id,
                "teacher_id": teacher_id,
                "section_id": section_id
            }
        }
