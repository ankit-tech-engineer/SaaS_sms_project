from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from app.core.database import get_database
from app.modules.academics.subjects.model import Subject
from app.modules.academics.subjects.schema import CreateSubjectRequest, UpdateSubjectRequest
import pymongo

class SubjectService:
    @staticmethod
    async def create_subject(org_id: str, school_id: str, user_id: str, class_id: str, data: CreateSubjectRequest):
        db = await get_database()
        
        # 0. Verify Class exists
        class_obj = await db["classes"].find_one({"_id": class_id, "school_id": school_id})
        if not class_obj:
            raise HTTPException(404, "Class not found")
        
        # 1. Check for Duplicate Name or Code in Class
        existing = await db["subjects"].find_one({
            "school_id": school_id,
            "class_id": class_id,
            "$or": [
                {"subject_name": data.subject_name},
                {"subject_code": data.subject_code}
            ],
            "status": "active"
        })
        if existing:
            raise HTTPException(400, "Subject with this name or code already exists in the class")

        # 2. Create Instance
        new_subject = Subject(
            org_id=org_id,
            school_id=school_id,
            class_id=class_id,
            created_by=user_id,
            subject_name=data.subject_name,
            subject_code=data.subject_code,
            is_optional=data.is_optional
        )
        
        # 3. Insert
        await db["subjects"].insert_one(new_subject.model_dump(by_alias=True))
        return new_subject

    @staticmethod
    async def get_subjects(
        school_id: str, 
        class_id: Optional[str] = None, 
        status: str = "active",
        page: int = 1,
        limit: int = 10,
        subject_name: Optional[str] = None,
        subject_code: Optional[str] = None,
        is_optional: Optional[bool] = None
    ):
        db = await get_database()
        query = {"school_id": school_id, "status": status}
        if class_id:
            query["class_id"] = class_id
        if subject_name:
            query["subject_name"] = {"$regex": subject_name, "$options": "i"}
        if subject_code:
            query["subject_code"] = {"$regex": subject_code, "$options": "i"}
        if is_optional is not None:
            query["is_optional"] = is_optional
            
        skip = (page - 1) * limit
            
        cursor = db["subjects"].find(query).sort("subject_name", 1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        total = await db["subjects"].count_documents(query)
        
        return items, total
    
    @staticmethod
    async def get_subject_by_id(school_id: str, subject_id: str):
        db = await get_database()
        subject = await db["subjects"].find_one({"_id": subject_id, "school_id": school_id})
        if not subject:
            raise HTTPException(404, "Subject not found")
        return subject

    @staticmethod
    async def update_subject(school_id: str, subject_id: str, data: UpdateSubjectRequest):
        db = await get_database()
        
        # Check existence
        existing_subject = await SubjectService.get_subject_by_id(school_id, subject_id)
        
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return existing_subject
            
        # Check uniqueness if name or code changing
        if "subject_name" in updates or "subject_code" in updates:
             name_check = updates.get("subject_name", existing_subject["subject_name"])
             code_check = updates.get("subject_code", existing_subject["subject_code"])
             
             dup = await db["subjects"].find_one({
                "school_id": school_id,
                "class_id": existing_subject["class_id"],
                "$or": [
                    {"subject_name": name_check},
                    {"subject_code": code_check}
                ],
                "_id": {"$ne": subject_id},
                "status": "active"
            })
             if dup:
                 raise HTTPException(400, "Subject with this name or code already exists in the class")

        updates["updated_at"] = datetime.utcnow()
        
        await db["subjects"].update_one(
            {"_id": subject_id},
            {"$set": updates}
        )
        
        return await SubjectService.get_subject_by_id(school_id, subject_id)
    
    @staticmethod
    async def change_status(school_id: str, subject_id: str, status: str):
        db = await get_database()
        await SubjectService.get_subject_by_id(school_id, subject_id)
        
        await db["subjects"].update_one(
            {"_id": subject_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return True
