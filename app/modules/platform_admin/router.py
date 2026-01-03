from fastapi import APIRouter, Depends
from app.modules.auth.schema import AdminUserResponse
from app.modules.auth.model import AdminUser
from app.core.dependencies import get_current_active_user
from app.utils.response import APIResponse

router = APIRouter()

@router.get("/profile", response_model=AdminUserResponse)
async def read_admin_profile(
    current_user: AdminUser = Depends(get_current_active_user)
):
    return APIResponse.success(current_user, "Profile retrieved successfully")
