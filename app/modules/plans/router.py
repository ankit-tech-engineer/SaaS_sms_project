from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import check_permissions
from app.core.permissions import Permission
from app.modules.plans.schema import PlanCreate, PlanUpdate, PlanResponse, PlanCreateResponse
from app.modules.plans.model import Plan
from app.utils.response import APIResponse
from datetime import datetime
from app.core.database import get_database

router = APIRouter()

@router.post("", response_model=PlanCreateResponse, dependencies=[Depends(check_permissions([Permission.MANAGE_PLANS]))])
async def create_plan(plan_in: PlanCreate):
    db = await get_database()
    
    # Check if plan exists (optional logic based on name and cycle)
    existing_plan = await db["plans"].find_one({"name": plan_in.plan_name, "billing_cycle": plan_in.billing_cycle})
    if existing_plan:
         raise HTTPException(status_code=400, detail="Plan already exists")

    new_plan = Plan(
        name=plan_in.plan_name,
        price=plan_in.price,
        billing_cycle=plan_in.billing_cycle,
        limits=plan_in.limits,
        features=plan_in.features
    )
    
    await db["plans"].insert_one(new_plan.model_dump(by_alias=True))
    
    return APIResponse.success({"id": new_plan.id, "status": "created"}, "Plan created successfully", status.HTTP_201_CREATED)

@router.get("", response_model=List[PlanResponse], dependencies=[Depends(check_permissions([Permission.MANAGE_PLANS, Permission.MANAGE_ORGS]))])
async def list_plans():
    db = await get_database()
    cursor = db["plans"].find()
    plans = await cursor.to_list(length=100)
    
    # Map 'name' from DB to 'plan_name' in schema because of alias
    results = []
    for p in plans:
        p_data = Plan(**p)
        # Manually constructing response to match aliases or rely on Pydantic's from_attributes/validation if possible
        # Here we map explicitly to match the schema field name 'plan_name' which expects 'name' from source if using aliases properly, but let's be safe.
        # Actually PlanResponse uses `name: str = Field(alias="plan_name")` which is for validation FROM alias.
        # But we are returning data. Let's just pass dictionaries with 'id' populated.
        
        # Plan model has 'name'. Schema has 'name' aliased as 'plan_name'.
        # If we return Plan model dict, name=...
        # FastAPI will dump it.
        # Let's adjust schema to simpler matching if needed, but 'Plan' model has 'name'.
        # 'PlanResponse' has `name`. It should work.
        results.append(p_data)
        
    return APIResponse.success(results, "Plans retrieved successfully")

@router.get("/{plan_id}", response_model=PlanResponse, dependencies=[Depends(check_permissions([Permission.MANAGE_PLANS, Permission.MANAGE_ORGS]))])
async def get_plan(plan_id: str):
    db = await get_database()
    plan = await db["plans"].find_one({"_id": plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return APIResponse.success(Plan(**plan), "Plan retrieved successfully")

@router.put("/{plan_id}", response_model=PlanResponse, dependencies=[Depends(check_permissions([Permission.MANAGE_PLANS]))])
async def update_plan(plan_id: str, plan_in: PlanUpdate):
    db = await get_database()
    
    plan = await db["plans"].find_one({"_id": plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    update_data = plan_in.model_dump(exclude_unset=True)
    
    # Map plan_name to name if present
    if "plan_name" in update_data:
        update_data["name"] = update_data.pop("plan_name")
        
    if update_data:
        update_data["updated_at"] = datetime.now()
        await db["plans"].update_one({"_id": plan_id}, {"$set": update_data})
        
    updated_plan = await db["plans"].find_one({"_id": plan_id})
    return APIResponse.success(Plan(**updated_plan), "Plan updated successfully")

@router.delete("/{plan_id}", dependencies=[Depends(check_permissions([Permission.MANAGE_PLANS]))])
async def delete_plan(plan_id: str):
    db = await get_database()
    result = await db["plans"].delete_one({"_id": plan_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return APIResponse.success(None, "Plan deleted successfully")
