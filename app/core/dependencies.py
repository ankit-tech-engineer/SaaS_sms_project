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
