from datetime import datetime
from typing import List, Optional
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status
from app.core.database import db
from app.modules.holidays.model import COLLECTION_NAME
from app.modules.holidays.schema import CreateHolidayRequest

class HolidayService:
    
    @staticmethod
    async def create_holiday(request: CreateHolidayRequest, org_id: str, school_id: str, created_by: str) -> dict:
        """
        Create a new holiday. Handles unique constraint on (school_id, date).
        """
        holiday_doc = request.model_dump()
        holiday_doc.update({
            "org_id": org_id,
            "school_id": school_id,
            "status": "active",
            "created_by": created_by,
            "created_at": datetime.utcnow()
        })
        
        database = db.get_db()
        try:
            result = await database[COLLECTION_NAME].insert_one(holiday_doc)
            holiday_doc["_id"] = str(result.inserted_id)
            return holiday_doc
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Holiday for date {request.date} already exists for this school."
            )

    @staticmethod
    async def list_holidays(school_id: str, month: Optional[str] = None) -> List[dict]:
        """
        List holidays for a school. 
        Optional filter: month (Format: YYYY-MM)
        """
        database = db.get_db()
        query = {"school_id": school_id, "status": "active"}
        
        if month:
            # Simple string regex match since date is stored as "YYYY-MM-DD"
            # ^2025-08.* matches 2025-08-15
            query["date"] = {"$regex": f"^{month}"}
            
        cursor = database[COLLECTION_NAME].find(query).sort("date", 1)
        holidays = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            holidays.append(doc)
            
        return holidays

    @staticmethod
    async def is_holiday(school_id: str, date: str) -> bool:
        """
        Internal Utility: Check if a specific date is a holiday.
        """
        database = db.get_db()
        holiday = await database[COLLECTION_NAME].find_one({
            "school_id": school_id,
            "date": date,
            "status": "active"
        })
        return True if holiday else False
