from app.core.database import db
import pymongo

COLLECTION_NAME = "student_attendance"

async def ensure_attendance_indexes():
    """
    Ensure unique index on (class_id, section_id, subject_id, date, academic_year)
    to prevent duplicate attendance records.
    Note: subject_id is part of the unique key. If it's null (Coordinator Mode), 
    it still works as a unique constraint in MongoDB.
    """
    if db.client:
        database = db.get_db()
        collection = database[COLLECTION_NAME]
        
        # Unique Index
        await collection.create_index(
            [
                ("school_id", pymongo.ASCENDING),
                ("class_id", pymongo.ASCENDING),
                ("section_id", pymongo.ASCENDING),
                ("subject_id", pymongo.ASCENDING), # Nullable
                ("date", pymongo.ASCENDING),
                ("academic_year", pymongo.ASCENDING)
            ],
            unique=True,
            name="unique_attendance_submission_idx"
        )
