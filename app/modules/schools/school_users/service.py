from app.core.database import get_database
from app.modules.schools.school_users.model import SchoolUser
from app.core.security_school import get_password_hash
import secrets
import string

class SchoolUserService:
    @staticmethod
    def generate_strong_password(length=12):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for i in range(length))

    @staticmethod
    async def create_school_admin(org_id: str, school_id: str, school_name: str, school_code: str, created_by: str) -> SchoolUser:
        db = await get_database()
        
        # 1. Generate Credentials
        email = f"admin@{school_code.lower()}.schoolapp.com"
        plain_password = SchoolUserService.generate_strong_password()
        hashed_password = get_password_hash(plain_password)
        
        # 2. Create User Object
        # Note: We store plain_password temporarily in the object to return it ONCE
        # It is NOT saved to DB because we use model_dump(exclude={'plain_password'}) or similar, 
        # But here we are manually inserting.
        
        school_admin = SchoolUser(
            org_id=org_id,
            school_id=school_id,
            name=f"{school_name} Admin",
            email=email,
            password=hashed_password,
            role="SCHOOL_ADMIN",
            permissions=["ALL_ACCESS"], # Placeholder for full permissions
            created_by=created_by
        )
        
        # 3. Insert into DB
        await db["school_users"].insert_one(school_admin.model_dump(by_alias=True))
        
        # 4. Attach plain password to object instance for immediate return (Monkey patch for transport)
        school_admin.password = plain_password 
        
        return school_admin
