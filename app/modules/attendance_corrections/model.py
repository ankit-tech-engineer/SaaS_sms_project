from datetime import datetime
from typing import Optional, Any
from app.core.database import db

COLLECTION_NAME = "attendance_corrections"

from uuid import uuid4

class AttendanceCorrectionModel:
    @staticmethod
    async def create_request(data: dict) -> dict:
        database = db.get_db()
        data["_id"] = f"att_cor_{uuid4().hex[:12]}"
        result = await database[COLLECTION_NAME].insert_one(data)
        return data

    @staticmethod
    async def get_by_id(correction_id: str, school_id: str) -> Optional[dict]:
        database = db.get_db()
        return await database[COLLECTION_NAME].find_one({
            "_id": correction_id,
            "school_id": school_id
        })

    @staticmethod
    async def get_pending_requests(
        school_id: str, 
        role: str,
        user_id: str,
        section_ids: Optional[list] = None
    ):
        """
        Fetch pending requests based on role.
        Teacher: Own requests? (Maybe not needed for workflow, but good for UI)
        Coordinator: Requests for their sections where status is REQUESTED
        Admin: Requests where status is COORDINATOR_APPROVED (or REQUESTED if bypassing?) -> Spec says Admin creates ADMIN_APPROVED status.
        Let's stick to the workflow: 
        - Coordinator sees REQUESTED
        - Admin sees COORDINATOR_APPROVED
        """
        database = db.get_db()
        query = {"school_id": school_id}
        
        if role == "SECTION_COORDINATOR":
            query["status"] = "REQUESTED"
            # TODO: Filter by section_ids if we store section_id in correction.
            # We store attendance_id/student_id. We might need to join or store section_id in correction for easier querying.
            # Current spec doesn't explicitly ask for section_id in correction, but highly recommended for filtering.
            # I will add section_id and class_id to the correction document for easier coordinator filtering.
            if section_ids:
                query["section_id"] = {"$in": section_ids}
                
        elif role == "SCHOOL_ADMIN":
            query["status"] = "COORDINATOR_APPROVED"
            
        elif role == "TEACHER":
             query["requested_by.user_id"] = user_id

        cursor = database[COLLECTION_NAME].find(query).sort("created_at", -1)
        return await cursor.to_list(length=100)
    
    @staticmethod
    async def get_all_requests(school_id: str):
        database = db.get_db()
        # Admin usually needs to see everything or filter? User said "fetch all".
        # We'll just return all for the school, perhaps filtered by recently updated?
        # Limiting to 100 recent for performance default.
        cursor = database[COLLECTION_NAME].find({"school_id": school_id}).sort("updated_at", -1)
        return await cursor.to_list(length=100)

    @staticmethod
    async def update_status(correction_id: str, updates: dict):
        database = db.get_db()
        await database[COLLECTION_NAME].update_one(
            {"_id": correction_id},
            {"$set": updates}
        )
