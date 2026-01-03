from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_current_active_user
from app.core.database import get_database
from app.core.permissions import Role
from app.utils.response import APIResponse
from app.modules.audit.schema import AuditLogList, AuditLogResponse

router = APIRouter()

@router.get("/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user)
):
    # Strict Role Check
    if current_user.get("role") != Role.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    
    db = await get_database()
    cursor = db["audit_logs"].find().sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    # Convert ObjectIds to strings for Pydantic
    for log in logs:
        log["_id"] = str(log["_id"])
        
    total = await db["audit_logs"].count_documents({})
    
    return APIResponse.success(
        {
            "items": logs,
            "total": total
        },
        "Audit logs retrieved successfully"
    )
