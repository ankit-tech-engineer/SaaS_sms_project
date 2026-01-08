from datetime import datetime
from fastapi import HTTPException
from app.core.database import get_database
from app.core.security_teacher import verify_password, get_password_hash, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.modules.teachers.teacher_auth.schema import TeacherLoginRequest, ChangePasswordRequest

from app.core.guards import validate_login_status

class TeacherAuthService:
    @staticmethod
    async def login(request: TeacherLoginRequest):
        db = await get_database()
        
        # 1. Find User
        user = await db["teacher_users"].find_one({"username": request.username})
        if not user:
            raise HTTPException(status_code=400, detail="Invalid username or password")
            
        # 2. Verify Password
        if not verify_password(request.password, user["password"]):
            raise HTTPException(status_code=400, detail="Invalid username or password")
            
        # 3. Validate Status Hierarchy (Fail Fast)
        await validate_login_status(
            db=db,
            org_id=user["org_id"],
            school_id=user["school_id"],
            user_status=user["status"],
            role="TEACHER"
        )
        
        # 3b. Validate Teacher Record specific status (Business Logic)
        teacher = await db["teachers"].find_one({"_id": user["teacher_id"]})
        if not teacher or teacher.get("status") != "active":
             raise HTTPException(status_code=403, detail="Teacher record is inactive")
             
        # 4. Check if Section Coordinator
        # We check the section_coordinators collection to see if this teacher is assigned active
        coordinator_record = await db["section_coordinators"].find_one({
            "teacher_id": user["teacher_id"],
            "status": "active"
        })
        is_coord = True if coordinator_record else False

        # 5. Update Last Login
        await db["teacher_users"].update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
        
        # 6. Generate Tokens
        access_token = create_access_token(
            subject=user["_id"],
            extra_claims={
                "org_id": user["org_id"],
                "school_id": user["school_id"],
                "teacher_id": user["teacher_id"],
                "role": "TEACHER",
                "is_section_coordinator": is_coord
            }
        )
        refresh_token = create_refresh_token(subject=user["_id"])
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "force_password_change": user.get("security", {}).get("force_password_change", False)
        }

    @staticmethod
    async def change_password(
        user_id: str,
        request: ChangePasswordRequest
    ):
        db = await get_database()
        user = await db["teacher_users"].find_one({"_id": user_id})
        
        if not user:
             raise HTTPException(status_code=404, detail="User not found")
             
        # Verify Old Password
        if not verify_password(request.old_password, user["password"]):
             raise HTTPException(status_code=400, detail="Incorrect old password")
             
        # Minimum Length Check
        if len(request.new_password) < 8:
             raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
             
        # Update Hash
        hashed_password = get_password_hash(request.new_password)
        
        await db["teacher_users"].update_one(
            {"_id": user_id},
            {"$set": {
                "password": hashed_password,
                "security.force_password_change": False,
                "security.password_changed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        return True
