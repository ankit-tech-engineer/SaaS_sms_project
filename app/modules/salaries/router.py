from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_school_user
from app.modules.salaries.schema import (
    SalaryStructureRequest, SalaryStructureResponse, 
    GenerateSalaryRequest, MarkPaidRequest, 
    SalaryListResponse, GenericResponse
)
from app.modules.salaries.service import SalaryService

router = APIRouter()

@router.post("/teachers/{teacher_id}/salary-structure", response_model=SalaryStructureResponse)
async def set_salary_structure(
    teacher_id: str,
    request: SalaryStructureRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Set or Update Salary Structure for a Teacher.
    """
    return await SalaryService.set_salary_structure(
        teacher_id=teacher_id,
        request=request,
        org_id=current_user["org_id"],
        school_id=current_user["school_id"]
    )

@router.post("/salaries/generate", response_model=GenericResponse)
async def generate_salaries(
    request: GenerateSalaryRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Generate Monthly Salaries for all active teachers.
    """
    result = await SalaryService.generate_monthly_salaries(
        request=request,
        org_id=current_user["org_id"],
        school_id=current_user["school_id"]
    )
    # Mapping loose dict to GenericResponse if needed, or return direct
    return {
        "success": result["success"],
        "message": result["message"]
    }

@router.get("/salaries", response_model=SalaryListResponse)
async def list_salaries(
    month: str = Query(..., description="YYYY-MM"),
    current_user: dict = Depends(get_current_school_user)
):
    """
    List salaries for a specific month.
    """
    data = await SalaryService.list_salaries(month, current_user["school_id"])
    return {
        "success": True,
        "data": data
    }

@router.post("/salaries/{salary_id}/pay", response_model=GenericResponse)
async def mark_salary_paid(
    salary_id: str,
    request: MarkPaidRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Mark a salary record as PAID.
    Locks the record.
    """
    return await SalaryService.mark_as_paid(
        salary_id=salary_id,
        request=request,
        school_id=current_user["school_id"]
    )
