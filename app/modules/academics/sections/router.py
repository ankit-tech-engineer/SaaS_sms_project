from fastapi import APIRouter, Depends, Query
from app.utils.response import APIResponse
from app.core.dependencies import get_current_school_user
from app.modules.academics.sections.schema import CreateSectionRequest, UpdateSectionRequest, SectionResponse
from app.modules.academics.sections.service import SectionService
from typing import Optional

# Note: We will mount this router such that it handles /school/classes/{class_id}/sections
router = APIRouter()

@router.get("/all-sections")
async def list_all_sections(
    status: str = "active",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    section_name: Optional[str] = None,
    class_id: Optional[str] = None, # Allow filtering by class_id here too if user wants
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    # Provide class_id=None to fetch all (or specific if filtered)
    items, total = await SectionService.get_sections(school_id, class_id, status, page, limit, section_name)
    
    meta = {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }
    return APIResponse.success([SectionResponse(**s) for s in items], "All sections retrieved", meta=meta)

@router.post("/{class_id}/sections")
async def create_section(
    class_id: str,
    data: CreateSectionRequest,
    current_user: dict = Depends(get_current_school_user)
):
    org_id = current_user["org_id"]
    school_id = current_user["school_id"]
    user_id = current_user["_id"]
    
    new_section = await SectionService.create_section(org_id, school_id, user_id, class_id, data)
    return APIResponse.success(SectionResponse(**new_section.model_dump(by_alias=True)), "Section created successfully")

@router.get("/{class_id}/sections")
async def list_sections(
    class_id: str,
    status: str = "active",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    section_name: Optional[str] = None,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    items, total = await SectionService.get_sections(school_id, class_id, status, page, limit, section_name)
    
    meta = {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }
    return APIResponse.success([SectionResponse(**s) for s in items], "Sections retrieved", meta=meta)

@router.get("/{class_id}/sections/{section_id}")
async def get_section(
    class_id: str,
    section_id: str,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    # We could validate that section belongs to class_id, but get_section_by_id mainly checks school ownership.
    # Service could be enhanced to check class_id consistency if strictly required.
    section = await SectionService.get_section_by_id(school_id, section_id)
    if section["class_id"] != class_id:
        # Consistency check
        from fastapi import HTTPException
        raise HTTPException(404, "Section not found in this class")
        
    return APIResponse.success(SectionResponse(**section), "Section retrieved")

from app.modules.academics.sections.schema import SectionStatusUpdate

@router.put("/{class_id}/sections/{section_id}")
async def update_section(
    class_id: str,
    section_id: str,
    data: UpdateSectionRequest,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    # Verify consistency 
    section = await SectionService.get_section_by_id(school_id, section_id)
    if section["class_id"] != class_id:
         from fastapi import HTTPException
         raise HTTPException(404, "Section not found in this class")
         
    updated = await SectionService.update_section(school_id, section_id, data)
    return APIResponse.success(SectionResponse(**updated), "Section updated")

@router.patch("/{class_id}/sections/{section_id}/status")
async def change_section_status(
    class_id: str,
    section_id: str,
    data: SectionStatusUpdate,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    # Verify consistency
    section = await SectionService.get_section_by_id(school_id, section_id)
    if section["class_id"] != class_id:
         from fastapi import HTTPException
         raise HTTPException(404, "Section not found in this class")

    await SectionService.change_status(school_id, section_id, data.status)
    return APIResponse.success(None, "Section status updated")
