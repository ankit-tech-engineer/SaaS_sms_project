from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.modules.org_auth.schema import OrgLogin, OrgTokenResponse, OrgProfile, OrgRefreshTokenRequest
from app.modules.org_auth.service import OrgAuthService
from app.core.security import create_access_token, create_refresh_token
from jose import jwt, JWTError
from app.core.config import settings
from app.core.dependencies import get_current_org_user
from app.utils.response import APIResponse
from datetime import timedelta

router = APIRouter()

@router.post("/login")
async def login(login_data: OrgLogin):
    user = await OrgAuthService.authenticate_org_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if user.status != "active":
         raise HTTPException(status_code=400, detail="User account is inactive")

    # Create Access Token using ORG_SECRET_KEY
    access_token_expires = timedelta(minutes=settings.ORG_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Extra claims
    claims = {
        "org_id": user.org_id,
        "role": user.role,
        "type": "ORG_USER"
    }
    
    access_token = create_access_token(
        subject=user.id, 
        expires_delta=access_token_expires, 
        secret_key=settings.ORG_SECRET_KEY,
        claims=claims
    )
    
    refresh_token = create_refresh_token(
        subject=user.id,
        secret_key=settings.ORG_SECRET_KEY
    )
    
    return APIResponse.success({
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "expires_in": settings.ORG_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }, "Login successful")

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Compatible endpoint for Swagger UI (Form Data -> Raw JSON)
    user = await OrgAuthService.authenticate_org_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if user.status != "active":
         raise HTTPException(status_code=400, detail="User account is inactive")

    access_token_expires = timedelta(minutes=settings.ORG_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    claims = {
        "org_id": user.org_id,
        "role": user.role,
        "type": "ORG_USER"
    }
    
    access_token = create_access_token(
        subject=user.id, 
        expires_delta=access_token_expires, 
        secret_key=settings.ORG_SECRET_KEY,
        claims=claims
    )
    
    refresh_token = create_refresh_token(
        subject=user.id,
        secret_key=settings.ORG_SECRET_KEY
    )
    
    # Return raw JSON for OAuth2 compliance
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ORG_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh-token")
async def refresh_token(request: OrgRefreshTokenRequest):
    try:
        payload = jwt.decode(request.refresh_token, settings.ORG_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if payload.get("type") != "refresh":
             raise HTTPException(status_code=401, detail="Invalid token type")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    # Verify user exists (We don't need to check org_id in refresh token specifically as user ID is unique enough, 
    # but we should fetch user to get current Org ID and Role for the new access token)
    from app.core.database import get_database
    db = await get_database()
    user = await db["org_users"].find_one({"_id": user_id, "status": "active"})
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
        
    # Generate new Access Token
    access_token_expires = timedelta(minutes=settings.ORG_ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {
        "org_id": user["org_id"],
        "role": user["role"],
        "type": "ORG_USER"
    }
    
    new_access_token = create_access_token(
        subject=user_id, 
        expires_delta=access_token_expires, 
        secret_key=settings.ORG_SECRET_KEY,
        claims=claims
    )
    
    return APIResponse.success({
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ORG_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }, "Token refreshed successfully")

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_org_user)):
    # current_user is a dict from find_one
    # Transform to OrgUser to strip password etc if needed, or just return safe fields
    # Schema OrgProfile handles filtering
    return APIResponse.success(OrgProfile(**current_user), "Profile retrieved successfully")
