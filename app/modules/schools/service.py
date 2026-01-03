from datetime import datetime
from app.core.database import get_database
from app.modules.schools.model import School, SchoolAddress, SchoolContact, SchoolSettings, SchoolBranding
from app.core.security_school import create_access_token
from app.modules.school_users.service import SchoolUserService
from app.modules.schools.schema import CreateSchoolRequest, UpdateSchoolRequest, SchoolCreationResponse, CreateSchoolAdminResponse

class SchoolService:
    @staticmethod
    async def create_school(org_id: str, created_by: str, school_data: CreateSchoolRequest) -> SchoolCreationResponse:
        db = await get_database()
        
        # 1. Check for duplicates (school_code unique per org)
        existing = await db["schools"].find_one({
            "org_id": org_id,
            "school_code": school_data.school_code
        })
        if existing:
            raise HTTPException(400, "School Code already exists in this organization")

        # 2. Check Subscription Limit
        # Priority: Active Subscription > Org Plan > Default (Limit 1)
        plan_id = None
        
        # Check active subscription
        subscription = await db["subscriptions"].find_one(
            {"org_id": org_id, "status": "active"},
            sort=[("created_at", -1)]
        )
        
        if subscription:
            plan_id = subscription["plan_id"]
        else:
            # Fallback to org plan
            org = await db["organizations"].find_one({"_id": org_id})
            if org and org.get("plan_id"):
                plan_id = org["plan_id"]
        
        max_schools = 1 # Default strict limit
        
        if plan_id:
            plan = await db["plans"].find_one({"_id": plan_id})
            if plan and "limits" in plan:
                max_schools = plan["limits"].get("max_schools", 1)
        
        current_count = await db["schools"].count_documents({"org_id": org_id})
        
        if current_count >= max_schools:
            raise HTTPException(403, f"School limit reached for your plan. Limit: {max_schools}")
        
        # 3. Construct School Object
        # Convert Request Schemas to Model Schemas
        address_data = school_data.address.model_dump(exclude_unset=True)
        contact_data = school_data.contact.model_dump(exclude_unset=True)
        settings_data = school_data.settings.model_dump(exclude_unset=True) if school_data.settings else {}
        branding_data = school_data.branding.model_dump(exclude_unset=True) if school_data.branding else {}
        
        new_school = School(
            org_id=org_id,
            created_by=created_by,
            school_name=school_data.school_name,
            school_code=school_data.school_code,
            address=SchoolAddress(**address_data),
            contact=SchoolContact(**contact_data),
            settings=SchoolSettings(**settings_data),
            branding=SchoolBranding(**branding_data)
        )
        
        # 4. Insert School
        try:
            await db["schools"].insert_one(new_school.model_dump(by_alias=True))
        except pymongo.errors.DuplicateKeyError:
             raise HTTPException(400, "Duplicate key error")
             
        # 5. Auto-Create School Admin
        try:
            admin_user = await SchoolUserService.create_school_admin(
                org_id=org_id,
                school_id=new_school.id,
                school_name=new_school.school_name,
                school_code=new_school.school_code,
                created_by=created_by
            )
        except Exception as e:
            # ROLLBACK SCHOOL IF USER CREATION FAILS
            await db["schools"].delete_one({"_id": new_school.id})
            raise HTTPException(500, f"Failed to create school admin: {str(e)}")
            
        # 6. Generate Token (Auto Login)
        access_token_expires = 3600 # 1 Hour
        access_token = create_access_token(
            subject=admin_user.id,
            extra_claims={
                "org_id": admin_user.org_id,
                "school_id": admin_user.school_id,
                "role": admin_user.role
            }
        )
        
        return SchoolCreationResponse(
            school_id=new_school.id,
            school_admin=CreateSchoolAdminResponse(
                email=admin_user.email,
                access_token=access_token,
                password=admin_user.password, # Plain text password from service return
                expires_in=access_token_expires
            )
        )

    @staticmethod
    async def get_schools(org_id: str):
        db = await get_database()
        cursor = db["schools"].find({"org_id": org_id})
        return await cursor.to_list(length=100)

    @staticmethod
    async def get_school_by_id(org_id: str, school_id: str):
        db = await get_database()
        school = await db["schools"].find_one({"_id": school_id, "org_id": org_id})
        if not school:
            raise HTTPException(404, "School not found")
        return school

    @staticmethod
    async def update_school(org_id: str, school_id: str, update_data: UpdateSchoolRequest):
        db = await get_database()
        
        # Fetch first to check ownership and status
        school = await SchoolService.get_school_by_id(org_id, school_id)
        if school.get("status") == "suspended":
            raise HTTPException(400, "Cannot update a suspended school")
            
        # Convert to dot notation for safe nested updates
        update_dict = update_data.model_dump(exclude_unset=True)
        date_updates = {"updated_at": datetime.utcnow()} # Should use aware datetime in production
        
        flattened_update = {}
        for key, value in update_dict.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flattened_update[f"{key}.{sub_key}"] = sub_value
            else:
                flattened_update[key] = value
                
        if not flattened_update:
            return school
            
        final_update = {**flattened_update, **date_updates}
        
        await db["schools"].update_one(
            {"_id": school_id},
            {"$set": final_update}
        )
        
        return await SchoolService.get_school_by_id(org_id, school_id)

    @staticmethod
    async def change_status(org_id: str, school_id: str, status: str):
        db = await get_database()
        # Verify exists
        await SchoolService.get_school_by_id(org_id, school_id)
        
        await db["schools"].update_one(
            {"_id": school_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return True

    @staticmethod
    async def set_default(org_id: str, school_id: str):
        db = await get_database()
        
        # Verify ownership
        await SchoolService.get_school_by_id(org_id, school_id)
        
        # Unset others
        await db["schools"].update_many(
            {"org_id": org_id},
            {"$set": {"is_default": False}}
        )
        
        # Set new default
        await db["schools"].update_one(
            {"_id": school_id},
            {"$set": {"is_default": True}}
        )
        return True
