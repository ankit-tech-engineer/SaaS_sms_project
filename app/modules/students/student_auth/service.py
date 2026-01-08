from datetime import datetime
from fastapi import HTTPException, status
from app.core.database import get_database
from app.core.security_student import verify_password, get_password_hash, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.modules.students.student_auth.schema import StudentLoginRequest, ChangePasswordRequest
from app.modules.students.student_users.model import StudentUser

from app.core.guards import validate_login_status

class StudentAuthService:
    @staticmethod
    async def login(request: StudentLoginRequest):
        db = await get_database()
        
        # 1. Find User
        user = await db["student_users"].find_one({"username": request.username})
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
            role="STUDENT"
        )
            
        # 3b. Check Student Record
        student = await db["students"].find_one({"_id": user["student_id"]})
        if not student or student.get("status") != "active":
             raise HTTPException(status_code=403, detail="Student record is inactive")
             
        # 4. Update Last Login
        await db["student_users"].update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
        
        # 5. Generate Tokens
        access_token = create_access_token(
            subject=user["_id"],
            extra_claims={
                "org_id": user["org_id"],
                "school_id": user["school_id"],
                "student_id": user["student_id"],
                "role": "STUDENT"
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
        user = await db["student_users"].find_one({"_id": user_id})
        
        if not user:
             raise HTTPException(status_code=404, detail="User not found")
             
        # Verify Old Password
        if not verify_password(request.old_password, user["password"]):
             raise HTTPException(status_code=400, detail="Incorrect old password")
             
        # New Password Validation (Simple check, can be expanded)
        if len(request.new_password) < 8:
             raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
             
        # Update Hash
        hashed_password = get_password_hash(request.new_password)
        
        await db["student_users"].update_one(
            {"_id": user_id},
            {"$set": {
                "password": hashed_password,
                "security.force_password_change": False,
                "security.password_changed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        return True
