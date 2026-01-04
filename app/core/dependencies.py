from typing import Annotated, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.modules.auth.service import AuthService
from app.modules.auth.model import AdminUser
from app.modules.auth.schema import TokenData
from app.core.permissions import Role, Permission

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/platform/auth/token", 
    scheme_name="Platform Admin Auth"
)

org_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/org/auth/token", 
    scheme_name="Organization User Auth"
)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await AuthService.get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[AdminUser, Depends(get_current_user)]
) -> AdminUser:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_permissions(required_permissions: List[Permission]):
    def permission_checker(current_user: Annotated[AdminUser, Depends(get_current_active_user)]):
        if Role.SUPER_ADMIN == current_user.role:
            return current_user
        
        for perm in required_permissions:
            if perm not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
        return current_user
    return permission_checker

# --- Org User Dependencies ---

from app.core.database import get_database

async def get_current_org_user(token: Annotated[str, Depends(org_oauth2_scheme)]) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode using ORG_SECRET_KEY
        payload = jwt.decode(token, settings.ORG_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        org_id: str = payload.get("org_id")
        
        if user_id is None or org_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    db = await get_database()
    user = await db["org_users"].find_one({"_id": user_id, "org_id": org_id, "status": "active"})
    
    if user is None:
        raise credentials_exception
        
    return user

# --- School User Dependencies ---

from app.core.security_school import decode_access_token

school_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/school/auth/token",
    scheme_name="School User Auth"
)

async def get_current_school_user(token: Annotated[str, Depends(school_oauth2_scheme)]) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
        
    user_id = payload.get("sub")
    school_id = payload.get("school_id")
    
    if not user_id or not school_id:
        raise credentials_exception
        
    db = await get_database()
    
    # 1. Check User
    user = await db["school_users"].find_one({"_id": user_id, "status": "active"})
    if not user:
        raise credentials_exception
        
    # 2. Check Context Enforcement (User must belong to the school in token)
    if user["school_id"] != school_id:
         raise HTTPException(status_code=403, detail="School Context Mismatch")

    # 3. Check School Status (CRITICAL: Block access if school is suspended)
    school = await db["schools"].find_one({"_id": school_id})
    if not school or school.get("status") != "active":
        raise HTTPException(status_code=403, detail="School is suspended or inactive")

    return user

# --- Student User Dependencies ---

from app.core.security_student import decode_access_token as decode_student_token

student_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/student/auth/token",
    scheme_name="Student User Auth"
)

async def get_current_student_user(token: Annotated[str, Depends(student_oauth2_scheme)]) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_student_token(token)
    if not payload:
        raise credentials_exception
        
    user_id = payload.get("sub")
    student_id = payload.get("student_id")
    school_id = payload.get("school_id")
    
    if not user_id or not student_id:
        raise credentials_exception
        
    db = await get_database()
    
    # 1. Check Student User (Auth)
    user = await db["student_users"].find_one({"_id": user_id, "status": "active"})
    if not user:
        raise credentials_exception
        
    # 2. Check Student Record (Business Data) - Must also be active
    student = await db["students"].find_one({"_id": student_id})
    if not student or student.get("status") != "active":
        raise HTTPException(status_code=403, detail="Student account is inactive")
        
    # 3. Check School Status - If school is down, student cannot login
    school = await db["schools"].find_one({"_id": school_id})
    if not school or school.get("status") != "active":
        raise HTTPException(status_code=403, detail="School is suspended or inactive")

    # Return combined data or just user, depending on need. Returning user for now.
    user["student_details"] = student
    return user

