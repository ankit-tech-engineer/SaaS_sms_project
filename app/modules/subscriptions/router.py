from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from app.core.dependencies import check_permissions
from app.core.permissions import Permission
from app.modules.subscriptions.schema import SubscriptionAssignRequest, SubscriptionAssignResponse
from app.modules.subscriptions.model import Subscription
from app.utils.response import APIResponse
from app.core.database import get_database

router = APIRouter()

@router.post("/assign", response_model=SubscriptionAssignResponse, dependencies=[Depends(check_permissions([Permission.MANAGE_PLANS, Permission.MANAGE_ORGS]))])
async def assign_subscription(sub_in: SubscriptionAssignRequest):
    db = await get_database()
    
    # Verify Org exists
    org = await db["organizations"].find_one({"_id": sub_in.org_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Verify Plan exists
    plan = await db["plans"].find_one({"_id": sub_in.plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    # Calculate validity (simplified logic)
    billing_cycle = plan.get("billing_cycle", "monthly")
    if billing_cycle == "yearly":
        valid_delta = timedelta(days=365)
    else:
        valid_delta = timedelta(days=30)
        
    valid_till = datetime.now() + valid_delta
    
    new_sub = Subscription(
        org_id=sub_in.org_id,
        plan_id=sub_in.plan_id,
        valid_till=valid_till
    )
    
    await db["subscriptions"].insert_one(new_sub.model_dump(by_alias=True))

    # Update Org with plan_id
    await db["organizations"].update_one(
        {"_id": sub_in.org_id},
        {"$set": {"plan_id": sub_in.plan_id}}
    )
    
    return APIResponse.success({
        "subscription_id": new_sub.id,
        "status": new_sub.status,
        "valid_till": new_sub.valid_till.date()
    }, "Subscription assigned successfully")

from app.utils.dependent_details import fetch_dependent_details

@router.get("", dependencies=[Depends(check_permissions([Permission.MANAGE_PLANS, Permission.MANAGE_ORGS]))])
async def list_subscriptions():
    db = await get_database()
    cursor = db["subscriptions"].find().sort("created_at", -1)
    subscriptions = await cursor.to_list(length=100)
    
    # Enrichment Config
    DEPENDENCY_MAP = {
      "org_id": {
          "collection": "organizations",
          "name_field": "org_name"
      },
      "plan_id": {
          "collection": "plans",
          "name_field": "name"
      }
    }
    
    enriched_data = await fetch_dependent_details(subscriptions, DEPENDENCY_MAP)
    
    return APIResponse.success(enriched_data, "Subscriptions retrieved successfully")
