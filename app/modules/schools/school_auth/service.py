from datetime import datetime
from fastapi import HTTPException, status
from app.core.database import get_database
from app.modules.schools.school_users.model import SchoolUser
from app.modules.schools.school_auth.schema import LoginRequest, TokenResponse, ChangePasswordRequest
from app.core.security_school import verify_password, create_access_token, get_password_hash, create_refresh_token, decode_refresh_token

from app.core.guards import validate_login_status

class SchoolAuthService:
    @staticmethod
    async def authenticate_user(login_data: LoginRequest) -> TokenResponse:
        db = await get_database()
        
        # 1. Find User
        user = await db["school_users"].find_one({"email": login_data.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        # 2. Verify Password
        if not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        # 3. Validate Status Hierarchy (Fail Fast)
        await validate_login_status(
            db=db,
            org_id=user["org_id"],
            school_id=user["school_id"],
            user_status=user.get("status"),
            role=user.get("role", "SCHOOL_ADMIN") 
        )
             
        # 5. Update Last Login
        await db["school_users"].update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
        
        # 6. Create Tokens
        access_token_expires = 3600 # 1 Hour
        access_token = create_access_token(
            subject=user["_id"],
            extra_claims={
                "org_id": user["org_id"],
                "school_id": user["school_id"],
                "role": user["role"]
            }
        )
        refresh_token = create_refresh_token(subject=user["_id"])
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=access_token_expires,
            user={
                "id": user["_id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "school_id": user["school_id"]
            }
        )

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> TokenResponse:
        # 1. Decode & Validate Token
        payload = decode_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
            
        user_id = payload.get("sub")
        if not user_id:
             raise HTTPException(status_code=401, detail="Invalid token subject")
             
        # 2. Verify User & Context
        db = await get_database()
        user = await db["school_users"].find_one({"_id": user_id})
        
        if not user:
             raise HTTPException(status_code=401, detail="User not found")
             
        if user.get("status") != "active":
            raise HTTPException(status_code=403, detail="User is inactive")
            
        # 3. Verify School
        school = await db["schools"].find_one({"_id": user["school_id"]})
        if not school or school.get("status") != "active":
             raise HTTPException(status_code=403, detail="School is suspended")
             
        # 4. Issue New Access Token
        # (We could rotate refresh token here too, but for now just access token)
        access_token_expires = 3600 # 1 Hour
        new_access_token = create_access_token(
            subject=user["_id"],
            extra_claims={
                "org_id": user["org_id"],
                "school_id": user["school_id"],
                "role": user["role"]
            }
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token, # Returning same refresh token (or new one if rotation implemented)
            expires_in=access_token_expires,
            user={
                "id": user["_id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "school_id": user["school_id"]
            }
        )
        
    @staticmethod
    async def change_password(user_id: str, payload: ChangePasswordRequest):
        db = await get_database()
        user = await db["school_users"].find_one({"_id": user_id})
        
        if not user:
            raise HTTPException(404, "User not found")
            
        if not verify_password(payload.old_password, user["password"]):
             raise HTTPException(400, "Incorrect old password")
             
        hashed_new_pass = get_password_hash(payload.new_password)
        
        await db["school_users"].update_one(
            {"_id": user_id},
            {"$set": {"password": hashed_new_pass, "updated_at": datetime.utcnow()}}
        )
        return True
