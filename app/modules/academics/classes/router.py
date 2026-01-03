from fastapi import APIRouter, Depends, Request, Query
from typing import Optional
from app.utils.response import APIResponse
from app.core.dependencies import get_current_school_user
from app.modules.academics.classes.schema import CreateClassRequest, UpdateClassRequest, ClassResponse, ClassStatusUpdate
from app.modules.academics.classes.service import ClassService

router = APIRouter()

@router.post("")
async def create_class(
    data: CreateClassRequest,
    current_user: dict = Depends(get_current_school_user)
):
    # Context extraction
    org_id = current_user["org_id"]
    school_id = current_user["school_id"]
    user_id = current_user["_id"]
    
    new_class = await ClassService.create_class(org_id, school_id, user_id, data)
    return APIResponse.success(ClassResponse(**new_class.model_dump(by_alias=True)), "Class created successfully")

@router.get("")
async def list_classes(
    status: str = "active",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    class_name: Optional[str] = None,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    items, total = await ClassService.get_classes(school_id, status, page, limit, class_name)
    
    meta = {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }
    
    return APIResponse.success([ClassResponse(**c) for c in items], "Classes retrieved", meta=meta)

@router.get("/{class_id}")
async def get_class(
    class_id: str,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    class_obj = await ClassService.get_class_by_id(school_id, class_id)
    return APIResponse.success(ClassResponse(**class_obj), "Class retrieved successfully")

@router.put("/{class_id}")
async def update_class(
    class_id: str,
    data: UpdateClassRequest,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    updated = await ClassService.update_class(school_id, class_id, data)
    return APIResponse.success(ClassResponse(**updated), "Class updated")

@router.patch("/{class_id}/status")
async def change_class_status(
    class_id: str,
    data: ClassStatusUpdate,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    await ClassService.change_status(school_id, class_id, data.status)
    return APIResponse.success(None, "Class status updated")
