from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_school_user
from app.modules.teachers.schema import CreateTeacherRequest, CreateTeacherResponse
from app.modules.teachers.service import TeacherService

router = APIRouter()

@router.post("/teachers", response_model=CreateTeacherResponse)
async def create_teacher(
    request: CreateTeacherRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Create a new teacher.
    - Creates teacher record
    - Creates teacher_user login
    - Returns temporary credentials
    """
    result = await TeacherService.create_teacher(
        request=request,
        org_id=current_user["org_id"],
        school_id=current_user["school_id"],
        created_by=current_user["_id"]
    )
    
    return {
        "success": True,
        "data": result
    }
