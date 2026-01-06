from enum import Enum
from typing import List

class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    SUPPORT = "SUPPORT"

class Permission(str, Enum):
    MANAGE_PLANS = "MANAGE_PLANS"
    MANAGE_ORGS = "MANAGE_ORGS"
    VIEW_ANALYTICS = "VIEW_ANALYTICS"
    MANAGE_USERS = "MANAGE_USERS"

# Role defaults
ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: [
        Permission.MANAGE_PLANS, 
        Permission.MANAGE_ORGS, 
        Permission.VIEW_ANALYTICS, 
        Permission.MANAGE_USERS
    ],
    Role.ADMIN: [
        Permission.MANAGE_ORGS,
        Permission.VIEW_ANALYTICS
    ]
}

# --- School/Teacher Permissions ---
from datetime import date
from app.core.database import db

async def is_section_coordinator(teacher_id: str, section_id: str, school_id: str) -> bool:
    """
    Verify if a teacher is the active coordinator for a section.
    """
    database = db.get_db()
    coordinator = await database["section_coordinators"].find_one({
        "teacher_id": teacher_id,
        "section_id": section_id,
        "school_id": school_id,
        "status": "active"
    })
    return True if coordinator else False

async def validate_teacher_assignment(
    teacher_id: str, 
    class_id: str, 
    section_id: str, 
    subject_id: str, 
    school_id: str,
    attendance_date: date
) -> bool:
    """
    Verify if a teacher is assigned to this subject/class/section.
    Handles PRIMARY and SUBSTITUTE roles.
    """
    database = db.get_db()
    
    # Check for PRIMARY assignment
    primary = await database["teacher_assignments"].find_one({
        "teacher_id": teacher_id,
        "class_id": class_id,
        "section_id": section_id,
        "subject_id": subject_id,
        "school_id": school_id,
        "role_type": "PRIMARY" 
    })
    
    if primary:
        return True
        
    # Check for SUBSTITUTE assignment
    substitute = await database["teacher_assignments"].find_one({
        "teacher_id": teacher_id,
        "class_id": class_id,
        "section_id": section_id,
        "subject_id": subject_id,
        "school_id": school_id,
        "role_type": "SUBSTITUTE"
    })
    
    if substitute:
        sub_from = substitute.get("substitute_from")
        sub_to = substitute.get("substitute_to")
        
        # Date comparison logic handling date objects or strings
        # Ideally we ensure format, but here we try to be robust
        check_date = attendance_date
        
        # Helper to convert to date object if string
        def to_date(d):
            if isinstance(d, str):
                return date.fromisoformat(d)
            if hasattr(d, "date"):
                return d.date()
            return d

        s_start = to_date(sub_from)
        s_end = to_date(sub_to)
        
        if s_start and s_end and s_start <= check_date <= s_end:
            return True

    return False
