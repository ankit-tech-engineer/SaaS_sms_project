from fastapi import APIRouter, Depends, HTTPException
from app.utils.response import APIResponse
from app.modules.school_auth.schema import LoginRequest, ChangePasswordRequest, SchoolUserResponse
from app.modules.school_auth.service import SchoolAuthService
from app.core.dependencies import get_current_school_user

router = APIRouter()

@router.post("/login")
async def login(login_data: LoginRequest):
    result = await SchoolAuthService.authenticate_user(login_data)
    return APIResponse.success(result.model_dump(), "Login successful")

# Refresh Token Endpoint
from app.modules.school_auth.schema import RefreshTokenRequest
@router.post("/refresh-token")
async def refresh_token(payload: RefreshTokenRequest):
    result = await SchoolAuthService.refresh_access_token(payload.refresh_token)
    return APIResponse.success(result.model_dump(), "Token refreshed successfully")

# Swagger UI / Token Endpoint (Form Data)
from fastapi.security import OAuth2PasswordRequestForm
@router.post("/token")
async def login_swagger(form_data: OAuth2PasswordRequestForm = Depends()):
    # Map Swagger content to our Login Request
    login_data = LoginRequest(email=form_data.username, password=form_data.password)
    result = await SchoolAuthService.authenticate_user(login_data)
    # Return as standard OAuth2 response (or our API Success wrapper if preferred, but Swagger expects specific JSON)
    # Standard OAuth2 response for tokenUrl is just JSON {access_token, token_type}
    return {"access_token": result.access_token, "token_type": result.token_type}

@router.get("/profile")
async def get_profile(
    current_user = Depends(get_current_school_user)
):
    # current_user is a dict or SchoolUser object depending on dependency impl.
    # Assuming dependency converts DB dict to schema or we do it here.
    return APIResponse.success(SchoolUserResponse(**current_user), "User profile retrieved")

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user = Depends(get_current_school_user)
):
    user_id = current_user["_id"] # Assuming dict
    await SchoolAuthService.change_password(user_id, payload)
    return APIResponse.success(None, "Password changed successfully")
