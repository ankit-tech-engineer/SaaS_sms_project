from datetime import timedelta
from typing import Optional
from app.core.database import get_database
from app.modules.auth.model import AdminUser
from app.modules.auth.schema import AdminUserCreate
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.core.permissions import Role, ROLE_PERMISSIONS

class AuthService:
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[AdminUser]:
        db = await get_database()
        user_data = await db["admin_users"].find_one({"email": email})
        if user_data:
            return AdminUser(**user_data)
        return None

    @staticmethod
    async def create_user(user_in: AdminUserCreate) -> AdminUser:
        db = await get_database()
        hashed_password = get_password_hash(user_in.password)
        
        # Get default permissions for role
        permissions = ROLE_PERMISSIONS.get(user_in.role, [])
        
        new_user = AdminUser(
            name=user_in.name,
            email=user_in.email,
            hashed_password=hashed_password,
            role=user_in.role,
            permissions=permissions
        )
        
        result = await db["admin_users"].insert_one(new_user.model_dump(by_alias=True))
        # Update ID with inserted ID just in case, though uuid is generated
        return new_user

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[AdminUser]:
        user = await AuthService.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def init_super_admin():
        email = settings.FIRST_SUPER_ADMIN_EMAIL
        user = await AuthService.get_user_by_email(email)
        if not user:
            print(f"Initializing Super Admin: {email}")
            super_admin = AdminUserCreate(
                name="Super Admin",
                email=email,
                password=settings.FIRST_SUPER_ADMIN_PASSWORD,
                role=Role.SUPER_ADMIN
            )
            await AuthService.create_user(super_admin)
            print("Super Admin created.")
        else:
            print("Super Admin already exists.")
