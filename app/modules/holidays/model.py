from app.core.database import db
import pymongo

COLLECTION_NAME = "school_holidays"

async def ensure_holiday_indexes():
    """
    Ensure unique index on (school_id, date) to prevent duplicate holidays
    for the same school on the same date.
    """
    if db.client:
        database = db.get_db()
        collection = database[COLLECTION_NAME]
        
        # Unique Index: school_id + date
        await collection.create_index(
            [("school_id", pymongo.ASCENDING), ("date", pymongo.ASCENDING)],
            unique=True,
            name="unique_school_date_idx"
        )
