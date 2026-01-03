from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from app.core.database import get_database
from app.modules.academics.sections.model import Section
from app.modules.academics.sections.schema import CreateSectionRequest, UpdateSectionRequest
import pymongo

class SectionService:
    @staticmethod
    async def create_section(org_id: str, school_id: str, user_id: str, class_id: str, data: CreateSectionRequest):
        db = await get_database()
        
        # 0. Verify Class exists and belongs to School
        class_obj = await db["classes"].find_one({"_id": class_id, "school_id": school_id})
        if not class_obj:
            raise HTTPException(404, "Class not found")
        
        # 1. Check for Duplicate Name in Class
        existing = await db["sections"].find_one({
            "school_id": school_id,
            "class_id": class_id,
            "section_name": data.section_name,
            "status": "active"
        })
        if existing:
            raise HTTPException(400, "Section with this name already exists in the class")

        # 2. Create Instance
        new_section = Section(
            org_id=org_id,
            school_id=school_id,
            class_id=class_id,
            created_by=user_id,
            section_name=data.section_name,
            capacity=data.capacity
        )
        
        # 3. Insert
        await db["sections"].insert_one(new_section.model_dump(by_alias=True))
        return new_section

    @staticmethod
    async def get_sections(
        school_id: str, 
        class_id: Optional[str] = None, 
        status: str = "active",
        page: int = 1,
        limit: int = 10,
        section_name: Optional[str] = None
    ):
        db = await get_database()
        
        query = {"school_id": school_id, "status": status}
        if class_id:
            query["class_id"] = class_id
        if section_name:
            query["section_name"] = {"$regex": section_name, "$options": "i"}
            
        skip = (page - 1) * limit
            
        cursor = db["sections"].find(query).sort("section_name", 1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        total = await db["sections"].count_documents(query)
        
        return items, total

    @staticmethod
    async def get_section_by_id(school_id: str, section_id: str):
        db = await get_database()
        section = await db["sections"].find_one({"_id": section_id, "school_id": school_id})
        if not section:
            raise HTTPException(404, "Section not found")
        return section

    @staticmethod
    async def update_section(school_id: str, section_id: str, data: UpdateSectionRequest):
        db = await get_database()
        
        # Check existence
        existing_section = await SectionService.get_section_by_id(school_id, section_id)
        
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return existing_section
            
        # Check uniqueness if name changing
        if "section_name" in updates and updates["section_name"] != existing_section["section_name"]:
             dup = await db["sections"].find_one({
                "school_id": school_id,
                "class_id": existing_section["class_id"],
                "section_name": updates["section_name"],
                "_id": {"$ne": section_id},
                "status": "active"
            })
             if dup:
                 raise HTTPException(400, "Section name already taken in this class")

        updates["updated_at"] = datetime.utcnow()
        
        await db["sections"].update_one(
            {"_id": section_id},
            {"$set": updates}
        )
        
        return await SectionService.get_section_by_id(school_id, section_id)

    @staticmethod
    async def change_status(school_id: str, section_id: str, status: str):
        db = await get_database()
        await SectionService.get_section_by_id(school_id, section_id)
        
        await db["sections"].update_one(
            {"_id": section_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return True
