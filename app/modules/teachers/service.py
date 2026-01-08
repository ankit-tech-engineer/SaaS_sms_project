import random
import string
from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from app.core.database import get_database
from app.core.security_teacher import get_password_hash
from app.modules.teachers.schema import CreateTeacherRequest
from app.modules.teachers.model import Teacher, PersonalInfo, ContactInfo, ProfessionalInfo
from app.modules.teachers.teacher_auth.model import TeacherUser, TeacherSecurity

class TeacherService:
    @staticmethod
    async def create_teacher(
        request: CreateTeacherRequest,
        org_id: str,
        school_id: str,
        created_by: str
    ):
        db = await get_database()
        
        # 1. Validation: Check if email already exists in this school (optional but good)
        # Assuming email should be unique per school or globally? 
        # For now, let's just proceed.
        
        # 2. Generate IDs
        teacher_id = f"teacher_{uuid4().hex[:12]}"
        teacher_user_id = f"tu_{uuid4().hex[:12]}"
        
        # 3. Generate Username (firstname.lastname)
        base_username = f"{request.personal.first_name.lower()}.{request.personal.last_name.lower()}"
        username = base_username
        
        # Simple uniqueness check loop
        counter = 1
        while await db["teacher_users"].find_one({"username": username}):
            username = f"{base_username}{counter}"
            counter += 1
            
        # 4. Generate Temporary Password
        temp_password_raw = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$", k=8))
        hashed_password = get_password_hash(temp_password_raw)
        
        # 5. Prepare Teacher Document
        # Handle Date conversions
        dob = request.personal.dob
        if isinstance(dob, (str, datetime.date)) and not isinstance(dob, datetime):
             # Ensure it's datetime for MongoDB
             if isinstance(dob, str):
                 dob = datetime.strptime(dob, "%Y-%m-%d") # Basic fallback
             else:
                 dob = datetime.combine(dob, datetime.min.time())

        joining_date = request.professional.joining_date
        if not joining_date:
            joining_date = datetime.utcnow()
        elif isinstance(joining_date, (str, datetime.date)) and not isinstance(joining_date, datetime):
             if isinstance(joining_date, str):
                 joining_date = datetime.strptime(joining_date, "%Y-%m-%d")
             else:
                 joining_date = datetime.combine(joining_date, datetime.min.time())

        teacher_doc = Teacher(
            _id=teacher_id,
            org_id=org_id,
            school_id=school_id,
            personal=PersonalInfo(
                first_name=request.personal.first_name,
                last_name=request.personal.last_name,
                gender=request.personal.gender,
                dob=dob
            ),
            contact=ContactInfo(
                mobile=request.contact.mobile,
                email=request.contact.email
            ),
            professional=ProfessionalInfo(
                qualification=request.professional.qualification,
                experience_years=request.professional.experience_years,
                joining_date=joining_date
            ),
            created_by=created_by
        )
        
        # 6. Prepare Teacher User Document
        teacher_user_doc = TeacherUser(
            _id=teacher_user_id,
            org_id=org_id,
            school_id=school_id,
            teacher_id=teacher_id,
            username=username,
            password=hashed_password,
            security=TeacherSecurity(force_password_change=True)
        )
        
        # 7. Atomic Write (Sequential in Mongo without transaction, technically not truly atomic without replicas, but acceptable for this context)
        # We will just insert.
        await db["teachers"].insert_one(teacher_doc.model_dump(by_alias=True))
        await db["teacher_users"].insert_one(teacher_user_doc.model_dump(by_alias=True))
        
        return {
            "teacher_id": teacher_id,
            "login": {
                "username": username,
                "temporary_password": temp_password_raw
            }
        }
