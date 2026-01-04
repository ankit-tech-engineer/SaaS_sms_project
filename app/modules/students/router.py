from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_school_user
from app.modules.students.schema import StudentAdmissionRequest, StudentAdmissionResponse
from app.modules.students.service import StudentService

router = APIRouter(prefix="/students")

@router.post("", response_model=StudentAdmissionResponse)
async def admit_student(
    request: StudentAdmissionRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Admit a new student.
    Only accessible by SCHOOL_ADMIN.
    """
    # Extract context from token (already validated by dependency)
    school_id = current_user["school_id"]
    org_id = current_user.get("org_id") # Should be in token
    user_id = current_user["_id"]
    
    # 1. Verify Role (Extra check, though dependency implies it if using specific scopes)
    # The prompt says: "Verify SCHOOL_ADMIN role". 
    # Current dependencies doesn't return role object for school user usually, just dict.
    # We should restart role check if needed, but assuming 'get_current_school_user' ensures valid school user.
    # Let's add explicit role check if 'role' field exists.
    if current_user.get("role") != "SCHOOL_ADMIN":
         raise HTTPException(status_code=403, detail="Only School Admins can admit students")

    result = await StudentService.admit_student(
        request=request,
        org_id=org_id,
        school_id=school_id,
        created_by=user_id
    )
    
    return {
        "success": True,
        "message": "Student admitted successfully",
        "data": result
    }
