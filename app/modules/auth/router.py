from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.modules.auth.schema import LoginRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.utils.response import APIResponse
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    user = await AuthService.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        subject=user.email
    )
    
    return APIResponse.success({
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }, "Login successful")

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await AuthService.authenticate_user(form_data.username, form_data.password)
    if not user:
        # Standard HTTPException for OAuth2 spec compatibility in Swagger UI
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        subject=user.email
    )
    
    # OAuth2 spec requires direct JSON for the token endpoint.
    # We return the raw dictionary here so Swagger UI and other standard OAuth2 clients can parse it correctly.
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
