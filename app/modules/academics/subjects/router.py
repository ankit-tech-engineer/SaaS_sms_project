from fastapi import APIRouter, Depends, Query
from app.utils.response import APIResponse
from app.core.dependencies import get_current_school_user
from app.modules.academics.subjects.schema import CreateSubjectRequest, UpdateSubjectRequest, SubjectResponse
from app.modules.academics.subjects.service import SubjectService
from typing import Optional

# Note: Mount at /school/classes/{class_id}/subjects
router = APIRouter()

@router.get("/all-subjects")
async def list_all_subjects(
    status: str = "active",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    subject_name: Optional[str] = None,
    subject_code: Optional[str] = None,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    items, total = await SubjectService.get_subjects(
        school_id, None, status, page, limit, subject_name, subject_code
    )
    
    meta = {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }
    return APIResponse.success([SubjectResponse(**s) for s in items], "All subjects retrieved", meta=meta)

@router.post("/{class_id}/subjects")
async def create_subject(
    class_id: str,
    data: CreateSubjectRequest,
    current_user: dict = Depends(get_current_school_user)
):
    org_id = current_user["org_id"]
    school_id = current_user["school_id"]
    user_id = current_user["_id"]
    
    new_subject = await SubjectService.create_subject(org_id, school_id, user_id, class_id, data)
    return APIResponse.success(SubjectResponse(**new_subject.model_dump(by_alias=True)), "Subject created successfully")

@router.get("/{class_id}/subjects")
async def list_subjects(
    class_id: str,
    status: str = "active",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    subject_name: Optional[str] = None, # Allow filtering within class too
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    items, total = await SubjectService.get_subjects(
        school_id, class_id, status, page, limit, subject_name
    )
    
    meta = {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }
    return APIResponse.success([SubjectResponse(**s) for s in items], "Subjects retrieved", meta=meta)

@router.get("/{class_id}/subjects/{subject_id}")
async def get_subject(
    class_id: str,
    subject_id: str,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    subject = await SubjectService.get_subject_by_id(school_id, subject_id)
    if subject["class_id"] != class_id:
        from fastapi import HTTPException
        raise HTTPException(404, "Subject not found in this class")
    return APIResponse.success(SubjectResponse(**subject), "Subject retrieved")

from app.modules.academics.subjects.schema import SubjectStatusUpdate

@router.put("/{class_id}/subjects/{subject_id}")
async def update_subject(
    class_id: str,
    subject_id: str,
    data: UpdateSubjectRequest,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    subject = await SubjectService.get_subject_by_id(school_id, subject_id)
    if subject["class_id"] != class_id:
        from fastapi import HTTPException
        raise HTTPException(404, "Subject not found in this class")

    updated = await SubjectService.update_subject(school_id, subject_id, data)
    return APIResponse.success(SubjectResponse(**updated), "Subject updated")

@router.patch("/{class_id}/subjects/{subject_id}/status")
async def change_subject_status(
    class_id: str,
    subject_id: str,
    data: SubjectStatusUpdate,
    current_user: dict = Depends(get_current_school_user)
):
    school_id = current_user["school_id"]
    subject = await SubjectService.get_subject_by_id(school_id, subject_id)
    if subject["class_id"] != class_id:
        from fastapi import HTTPException
        raise HTTPException(404, "Subject not found in this class")

    await SubjectService.change_status(school_id, subject_id, data.status)
    return APIResponse.success(None, "Subject status updated")
