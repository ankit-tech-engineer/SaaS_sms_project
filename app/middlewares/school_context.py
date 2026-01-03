from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.database import db

class SchoolContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Apply only to /school/* routes (future scope, but good to have ready)
        # OR if we want to enforce it on generic routes that might need school context.
        # For now, let's assume this applies when the path starts with /school
        # BUT: Exclude Auth routes (login/profile) which use Tokens instead of Headers
        
        if request.url.path.startswith("/school") and not request.url.path.startswith("/school/auth"):
            school_id = request.headers.get("X-School-Id")
            
            if not school_id:
                 return JSONResponse(status_code=400, content={"success": False, "message": "X-School-Id header missing", "error": True})
            
            # Org Context must already be present (OrgContextMiddleware runs before this)
            org_id = getattr(request.state, "org_id", None)
            if not org_id:
                return JSONResponse(status_code=403, content={"success": False, "message": "Organization Context Missing", "error": True})

            # Verify School
            database = db.get_db()
            school = await database["schools"].find_one({"_id": school_id, "org_id": org_id})
            
            if not school:
                return JSONResponse(status_code=404, content={"success": False, "message": "School not found or access denied", "error": True})
            
            if school.get("status") != "active":
                 return JSONResponse(status_code=403, content={"success": False, "message": "School is not active", "error": True})
            
            # Inject into state
            request.state.school_id = school_id
            request.state.school = school
            
        return await call_next(request)
