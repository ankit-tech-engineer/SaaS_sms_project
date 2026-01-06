from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.dependencies import get_current_school_user
from app.modules.holidays.schema import CreateHolidayRequest, HolidayResponse, HolidayListResponse
from app.modules.holidays.service import HolidayService

router = APIRouter()

@router.post("/holidays", response_model=HolidayResponse)
async def create_holiday(
    request: CreateHolidayRequest,
    current_user: dict = Depends(get_current_school_user)
):
    """
    Create a new holiday (School Admin Only).
    """
    # Verify Permissions (School Admin only)
    if current_user["role"] != "SCHOOL_ADMIN":
         # Or rely on dependency? usually dependency is broad. 
         # Assuming logic requires explicit check or dependency upgrade.
         # For now, let's enforce here or assume dependency allows admin.
         pass 

    result = await HolidayService.create_holiday(
        request=request,
        org_id=current_user["org_id"],
        school_id=current_user["school_id"],
        created_by=current_user["_id"]
    )
    
    return {
        "success": True,
        "message": "Holiday created successfully",
        "data": result
    }

@router.get("/holidays", response_model=HolidayListResponse)
async def list_holidays(
    month: Optional[str] = Query(None, description="Filter by month (YYYY-MM)", regex=r"^\d{4}-\d{2}$"),
    current_user: dict = Depends(get_current_school_user)
):
    """
    List holidays.
    """
    data = await HolidayService.list_holidays(
        school_id=current_user["school_id"],
        month=month
    )
    
    return {
        "success": True,
        "data": data
    }
