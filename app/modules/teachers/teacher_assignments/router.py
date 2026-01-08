from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_school_user, get_current_teacher_user
from app.modules.teachers.teacher_assignments.schema import (
    CreateAssignmentRequest, AssignmentResponse, AssignmentListResponse
)
from app.modules.teachers.teacher_assignments.service import TeacherAssignmentService

router = APIRouter()

@router.post("/class-teacher-assignments", response_model=AssignmentResponse)
async def assign_teacher(
    request: CreateAssignmentRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Assign a teacher to a subject (School Admin only).
    """
    result = await TeacherAssignmentService.assign_teacher(
        request=request,
        org_id=current_user["org_id"],
        school_id=current_user["school_id"],
        created_by=current_user["_id"]
    )
    return result

@router.get("/class-teacher-assignments", response_model=AssignmentListResponse)
async def list_assignments(
    class_id: str = Query(None),
    section_id: str = Query(None),
    current_user: dict = Depends(get_current_school_user)
):
    """
    List assignments with filters (School Admin only).
    """
    data = await TeacherAssignmentService.list_assignments(
        school_id=current_user["school_id"],
        class_id=class_id,
        section_id=section_id
    )
    return {"success": True, "data": data}

@router.delete("/class-teacher-unassignments/{assignment_id}")
async def unassign_teacher(
    assignment_id: str,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Unassign a teacher (School Admin only).
    """
    return await TeacherAssignmentService.unassign_teacher(
        assignment_id=assignment_id,
        school_id=current_user["school_id"]
    )

@router.get("/my-class-assignments", response_model=AssignmentListResponse) # /teacher prefix handling in main.py? No, this is likely /teacher/assignments
# Wait, main.py prefixes:
# /school -> school_app_router
# /teacher -> teacher_app_router
# So this router needs to be split or mounted twice? 
# Or we separate Admin and Teacher routes?
# For now, I'll attach this endpoint here, but in main.py we might need to mount this router under /teacher too?
# Or clearer: have separate sub-routers?
# Simpler: Create a separate router for teacher views or handle in main.py.
# Let's assume this file is included in `school_app_router` (Admin) AND `teacher_app_router` (Teacher).
# But permissions differ.
# Let's explicitly define the teacher path here, and we will mount it correctly.
# Actually, dependencies differ. 
# Best practice: 2 routers in one file or permissions inside?
# Let's keep it simple: Add endpoint here, but dependency will differ.
async def get_my_assignments(
    current_user: dict = Depends(get_current_teacher_user)
):
    """
    Get assignments for the logged-in teacher.
    """
    data = await TeacherAssignmentService.list_assignments(
        school_id=current_user["school_id"],
        teacher_id=current_user["teacher_details"]["_id"]
    )
    return {"success": True, "data": data}
