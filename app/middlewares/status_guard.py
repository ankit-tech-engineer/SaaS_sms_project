from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request, status
from app.core.database import db

class StatusGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Skip Auth endpoints (Login status is handled by AuthService)
        if "/auth/" in request.url.path or "/docs" in request.url.path or "/openapi.json" in request.url.path:
            return await call_next(request)

        # 2. Extract Context (Assume populated by Auth/Context middlewares running before this)
        # Note: In Starlette/FastAPI, middlewares added LATER run FIRST.
        # So we will add this Middleware AFTER Auth/Context middlewares in main.py
        # to ensure it runs INNER (after context is set).
        # WAIT. Usually: Request -> Middleware A -> Middleware B -> Route.
        # If we Add A then B. Request hits B then A.
        # We need Auth (outer) -> Status (inner).
        # So we must Add Status (inner) FIRST, then Auth (outer).
        # NO. "add_middleware" adds to the outer layer.
        # So we add StatusGuard, then Auth. 
        # Result: Request -> Auth -> StatusGuard -> Route.
        
        # ACTUALLY: Let's rely on request.state.
        
        org_id = getattr(request.state, "org_id", None)
        school_id = getattr(request.state, "school_id", None)
        user_role = getattr(request.state, "role", None) # Or however we store it
        # SchoolUserContext stores: request.state.school_user = { role: ... }
        # AuthMiddleware stores: user_id (sub)
        
        # We need to standardize how we get Role.
        # Let's check common locations.
        school_user = getattr(request.state, "school_user", None)
        if not user_role and school_user:
            user_role = school_user.get("role")
        
        # If no org_id, maybe it's a super admin or public route?
        # If public route, we might skip?
        # But even public routes might belong to an Org (e.g. /org/...).
        # OrgContext middleware sets org_id.
        
        if org_id:
            database = db.get_db()
            
            # --- 1. Check Org Status ---
            # Optimization: Cache this? For now, direct DB.
            org = await database["organizations"].find_one({"_id": org_id})
            if not org or org.get("status") != "active":
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"success": False, "message": "Organization is inactive or suspended", "error": True}
                )

            # --- 2. Check School Status ---
            if school_id:
                school = await database["schools"].find_one({"_id": school_id})
                if not school or school.get("status") != "active":
                    # Inactive School Rule:
                    # Admin -> Read Only
                    # Others -> Block
                    
                    is_admin = user_role in ["SCHOOL_ADMIN", "ADMIN", "SUPER_ADMIN"] # Adapt roles as needed
                    
                    if is_admin:
                        if request.method not in ["GET", "OPTIONS", "HEAD"]:
                             return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={"success": False, "message": "School is inactive. Read-only mode active.", "error": True}
                            )
                    else:
                        # Teacher / Student
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"success": False, "message": "School is inactive. Access denied.", "error": True}
                        )

        # Proceed
        response = await call_next(request)
        return response
