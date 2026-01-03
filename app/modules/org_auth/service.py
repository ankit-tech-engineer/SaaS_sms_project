from datetime import datetime, timedelta
from app.core.database import get_database
from app.modules.org_auth.model import OrgUser
from app.core.security import verify_password, get_password_hash
from app.core.config import settings

class OrgAuthService:
    @staticmethod
    async def create_org_user(user_data: dict) -> OrgUser:
        db = await get_database()
        
        # Hash password
        user_data["password"] = get_password_hash(user_data["password"])
        
        new_user = OrgUser(**user_data)
        await db["org_users"].insert_one(new_user.model_dump(by_alias=True))
        return new_user

    @staticmethod
    async def authenticate_org_user(email: str, password: str):
        db = await get_database()
        user_data = await db["org_users"].find_one({"email": email})
        
        if not user_data:
            return None
            
        if not verify_password(password, user_data["password"]):
            return None
            
        # Update last login
        await db["org_users"].update_one(
            {"_id": user_data["_id"]},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
            
        return OrgUser(**user_data)
