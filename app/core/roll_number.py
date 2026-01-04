from app.core.database import get_database

async def generate_next_roll_number(
    school_id: str,
    class_id: str,
    section_id: str,
    academic_year: str
) -> int:
    """
    Atomically generates the next roll number for a given section in an academic year.
    Uses a separate 'sequences' collection to ensure uniqueness and concurrency safety.
    """
    db = await get_database()
    
    # Key to uniquely identify the sequence
    sequence_key = f"{school_id}_{academic_year}_{class_id}_{section_id}_roll_no"
    
    result = await db["sequences"].find_one_and_update(
        {"_id": sequence_key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    
    return result["seq"]
