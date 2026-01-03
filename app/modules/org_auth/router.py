from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.modules.org_auth.schema import OrgLogin, OrgTokenResponse, OrgProfile
from app.modules.org_auth.service import OrgAuthService
from app.core.security import create_access_token
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
    
    return APIResponse.success({
        "access_token": access_token, 
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
    
    # Return raw JSON for OAuth2 compliance
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.ORG_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_org_user)):
    # current_user is a dict from find_one
    # Transform to OrgUser to strip password etc if needed, or just return safe fields
    # Schema OrgProfile handles filtering
    return APIResponse.success(OrgProfile(**current_user), "Profile retrieved successfully")
