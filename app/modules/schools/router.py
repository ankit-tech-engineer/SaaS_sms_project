from fastapi import APIRouter, Depends, Request, HTTPException
from app.core.dependencies import get_current_org_user
from typing import List
from app.utils.response import APIResponse
from app.modules.schools.schema import CreateSchoolRequest, SchoolResponse, UpdateSchoolRequest, SchoolStatusUpdate
from app.modules.schools.service import SchoolService

router = APIRouter()

# Validation Dependency
def validate_org_context(
    request: Request,
    current_user: dict = Depends(get_current_org_user)
):
    if not hasattr(request.state, "org_id") or not request.state.org_id:
        raise HTTPException(403, "Organization Context Missing")
    return request.state.org_id

@router.post("")
async def create_school(
    school_data: CreateSchoolRequest,
    request: Request,
    org_id: str = Depends(validate_org_context)
):
    user_id = request.state.user_id
    creation_result = await SchoolService.create_school(org_id, user_id, school_data)
    return APIResponse.success(creation_result.model_dump(), "School created and logged in successfully")

@router.get("")
async def list_schools(
    org_id: str = Depends(validate_org_context)
):
    schools = await SchoolService.get_schools(org_id)
    return APIResponse.success([SchoolResponse(**s) for s in schools], "Schools retrieved")

@router.get("/{school_id}")
async def get_school(
    school_id: str,
    org_id: str = Depends(validate_org_context)
):
    school = await SchoolService.get_school_by_id(org_id, school_id)
    return APIResponse.success(SchoolResponse(**school), "School details")

@router.put("/{school_id}")
async def update_school(
    school_id: str,
    update_data: UpdateSchoolRequest,
    org_id: str = Depends(validate_org_context)
):
    school = await SchoolService.update_school(org_id, school_id, update_data)
    return APIResponse.success(SchoolResponse(**school), "School updated")

@router.patch("/{school_id}/status")
async def change_status(
    school_id: str,
    status_data: SchoolStatusUpdate,
    org_id: str = Depends(validate_org_context)
):
    await SchoolService.change_status(org_id, school_id, status_data.status)
    return APIResponse.success(None, f"School status updated to {status_data.status}")

@router.patch("/{school_id}/default")
async def set_default_school(
    school_id: str,
    org_id: str = Depends(validate_org_context)
):
    await SchoolService.set_default(org_id, school_id)
    return APIResponse.success(None, "Default school updated")
