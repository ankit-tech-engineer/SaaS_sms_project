from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from app.core.database import get_database
from app.modules.academics.classes.model import Class
from app.modules.academics.classes.schema import CreateClassRequest, UpdateClassRequest
import pymongo

class ClassService:
    @staticmethod
    async def create_class(org_id: str, school_id: str, user_id: str, data: CreateClassRequest):
        db = await get_database()
        
        # 1. Check for Duplicate Name in School
        existing = await db["classes"].find_one({
            "school_id": school_id,
            "class_name": data.class_name,
            "status": "active" # Only check against active classes? Or all? Usually names should be unique globally within school to avoid confusion.
            # Let's check globally within school for now, or at least active/archived.
        })
        if existing:
            raise HTTPException(400, "Class with this name already exists in the school")

        # 2. Create Instance
        new_class = Class(
            org_id=org_id,
            school_id=school_id,
            created_by=user_id,
            class_name=data.class_name,
            class_order=data.class_order
        )
        
        # 3. Insert
        await db["classes"].insert_one(new_class.model_dump(by_alias=True))
        return new_class

    @staticmethod
    async def get_classes(school_id: str, status: str = "active", page: int = 1, limit: int = 10, class_name: Optional[str] = None):
        db = await get_database()
        
        query = {"school_id": school_id, "status": status}
        if class_name:
            query["class_name"] = {"$regex": class_name, "$options": "i"}
            
        skip = (page - 1) * limit
        
        cursor = db["classes"].find(query).sort("class_order", 1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        total = await db["classes"].count_documents(query)
        
        return items, total

    @staticmethod
    async def get_class_by_id(school_id: str, class_id: str):
        db = await get_database()
        class_obj = await db["classes"].find_one({"_id": class_id, "school_id": school_id})
        if not class_obj:
            raise HTTPException(404, "Class not found")
        return class_obj

    @staticmethod
    async def update_class(school_id: str, class_id: str, data: UpdateClassRequest):
        db = await get_database()
        
        # Check existence
        existing_class = await ClassService.get_class_by_id(school_id, class_id)
        
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return existing_class
            
        # Check uniqueness if name changing
        if "class_name" in updates and updates["class_name"] != existing_class["class_name"]:
             dup = await db["classes"].find_one({
                "school_id": school_id,
                "class_name": updates["class_name"],
                "_id": {"$ne": class_id}
            })
             if dup:
                 raise HTTPException(400, "Class name already taken")

        updates["updated_at"] = datetime.utcnow()
        
        await db["classes"].update_one(
            {"_id": class_id},
            {"$set": updates}
        )
        
        return await ClassService.get_class_by_id(school_id, class_id)

    @staticmethod
    async def change_status(school_id: str, class_id: str, status: str):
        db = await get_database()
        await ClassService.get_class_by_id(school_id, class_id)
        
        await db["classes"].update_one(
            {"_id": class_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return True
