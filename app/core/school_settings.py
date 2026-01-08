from typing import Optional, Literal
from app.core.database import db

COLLECTION_NAME = "school_settings"
DEFAULT_MODE = "COORDINATOR_ONLY"

class SchoolSettings:
    
    @staticmethod
    async def get_attendance_policy(school_id: str) -> dict:
        """
        Fetch attendance policy for a school. 
        Returns full configuration:
        {
            "mode": "COORDINATOR_ONLY" | "SUBJECT_TEACHER",
            "past_attendance_days_allowed": int (default 0)
        }
        """
        database = db.get_db()
        settings = await database[COLLECTION_NAME].find_one({"school_id": school_id})
        
        default_policy = {
            "mode": DEFAULT_MODE,
            "past_attendance_days_allowed": 0
        }
        
        if settings and "attendance_policy" in settings:
             policy = settings["attendance_policy"]
             # Merge with defaults to ensure all keys exist
             return {**default_policy, **policy}
        
        return default_policy

    @staticmethod
    async def set_attendance_policy(
        school_id: str, 
        mode: Literal["COORDINATOR_ONLY", "SUBJECT_TEACHER"],
        past_attendance_days_allowed: int = 0
    ):
        """
        Update or Create attendance policy.
        """
        database = db.get_db()
        await database[COLLECTION_NAME].update_one(
            {"school_id": school_id},
            {"$set": {
                "attendance_policy": {
                    "mode": mode,
                    "past_attendance_days_allowed": past_attendance_days_allowed
                }
            }},
            upsert=True
        )
