from typing import Optional, Literal
from app.core.database import db

COLLECTION_NAME = "school_settings"
DEFAULT_MODE = "COORDINATOR_ONLY"

class SchoolSettings:
    
    @staticmethod
    async def get_attendance_policy(school_id: str) -> str:
        """
        Fetch attendance policy for a school. 
        Defaults to COORDINATOR_ONLY if not set.
        Returns: "COORDINATOR_ONLY" | "SUBJECT_TEACHER"
        """
        database = db.get_db()
        settings = await database[COLLECTION_NAME].find_one({"school_id": school_id})
        
        if settings and "attendance_policy" in settings:
             return settings["attendance_policy"].get("mode", DEFAULT_MODE)
        
        return DEFAULT_MODE

    @staticmethod
    async def set_attendance_policy(school_id: str, mode: Literal["COORDINATOR_ONLY", "SUBJECT_TEACHER"]):
        """
        Update or Create attendance policy.
        """
        database = db.get_db()
        await database[COLLECTION_NAME].update_one(
            {"school_id": school_id},
            {"$set": {"attendance_policy": {"mode": mode}}},
            upsert=True
        )
