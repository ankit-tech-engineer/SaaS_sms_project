from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.dependencies import get_current_school_user
from app.modules.teachers.section_coordinators.service import SectionCoordinatorService

router = APIRouter()

class AssignCoordinatorRequest(BaseModel):
    teacher_id: str

@router.post("/sections/{section_id}/assign-coordinator")
async def assign_coordinator(
    section_id: str,
    request: AssignCoordinatorRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Assign a teacher as Section Coordinator.
    - Removes existing coordinator for the section if any.
    - Validates teacher is not already a coordinator elsewhere.
    """
    result = await SectionCoordinatorService.assign_coordinator(
        section_id=section_id,
        teacher_id=request.teacher_id,
        org_id=current_user["org_id"],
        school_id=current_user["school_id"]
    )
    
    return result
