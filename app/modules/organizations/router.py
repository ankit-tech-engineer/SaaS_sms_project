from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.modules.organizations.schema import OrgSignupRequest, OrgSignupResponse, OrgResponse, OrgUpdate
from app.modules.organizations.model import Organization
from app.modules.organizations.org_auth.service import OrgAuthService
from app.utils.response import APIResponse
from app.core.database import get_database
from app.core.dependencies import check_permissions
from app.core.permissions import Permission
from datetime import datetime

router = APIRouter()

# Public signup
@router.post("/signup", response_model=OrgSignupResponse)
async def org_signup(org_in: OrgSignupRequest):
    db = await get_database()
    
    # Check simple duplicate on email
    existing = await db["organizations"].find_one({"email": org_in.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_org = Organization(
        org_name=org_in.org_name,
        owner_name=org_in.owner_name,
        email=org_in.email,
        mobile=org_in.mobile
    )
    
    # 1. Create Organization First
    await db["organizations"].insert_one(new_org.model_dump(by_alias=True))
    
    # 2. Create Org Owner User
    user_data = {
        "org_id": new_org.id,
        "name": org_in.owner_name,
        "email": org_in.email,
        "password": org_in.password,
        "mobile": org_in.mobile,
        "role": "ORG_OWNER",
        "permissions": ["MANAGE_SCHOOLS", "VIEW_BILLING"] # Default owner permissions
    }
    
    try:
        new_user = await OrgAuthService.create_org_user(user_data)
        
        # 3. Update Org with owner_user_id
        await db["organizations"].update_one(
            {"_id": new_org.id},
            {"$set": {"owner_user_id": new_user.id}}
        )
        
    except Exception as e:
        # Rollback org creation if user creation fails
        await db["organizations"].delete_one({"_id": new_org.id})
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")
    
    return APIResponse.success({
        "org_id": new_org.id,
        "owner_user_id": new_user.id,
        "trial_days": new_org.trial_days,
        "status": new_org.status
    }, "Organization signed up successfully", 201)

# Protected CRUD
@router.get("", response_model=List[OrgResponse], dependencies=[Depends(check_permissions([Permission.MANAGE_ORGS]))])
async def list_organizations():
    db = await get_database()
    cursor = db["organizations"].find()
    orgs = await cursor.to_list(length=100)
    return APIResponse.success([Organization(**org) for org in orgs], "Organizations retrieved successfully")

@router.get("/{org_id}", response_model=OrgResponse, dependencies=[Depends(check_permissions([Permission.MANAGE_ORGS]))])
async def get_organization(org_id: str):
    db = await get_database()
    org = await db["organizations"].find_one({"_id": org_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return APIResponse.success(Organization(**org), "Organization retrieved successfully")

@router.put("/{org_id}", response_model=OrgResponse, dependencies=[Depends(check_permissions([Permission.MANAGE_ORGS]))])
async def update_organization(org_id: str, org_in: OrgUpdate):
    db = await get_database()
    
    org = await db["organizations"].find_one({"_id": org_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    update_data = org_in.model_dump(exclude_unset=True)
    
    if update_data:
        # Check email uniqueness if email is being updated
        if "email" in update_data and update_data["email"] != org["email"]:
             existing = await db["organizations"].find_one({"email": update_data["email"]})
             if existing:
                 raise HTTPException(status_code=400, detail="Email already registered")
        
        await db["organizations"].update_one({"_id": org_id}, {"$set": update_data})
        
    updated_org = await db["organizations"].find_one({"_id": org_id})
    return APIResponse.success(Organization(**updated_org), "Organization updated successfully")

@router.delete("/{org_id}", dependencies=[Depends(check_permissions([Permission.MANAGE_ORGS]))])
async def delete_organization(org_id: str):
    db = await get_database()
    result = await db["organizations"].delete_one({"_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return APIResponse.success(None, "Organization deleted successfully")
