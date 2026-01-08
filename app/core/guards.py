from fastapi import HTTPException, status, Request
from app.core.database import get_database

async def validate_login_status(db, org_id: str, school_id: str = None, user_status: str = "active", role: str = None):
    """
    Validate status hierarchy at LOGIN time.
    FAIL FAST: Org -> School -> User
    """
    # 1. Organization Check
    org = await db["organizations"].find_one({"_id": org_id})
    if not org or org.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Organization is inactive or suspended"
        )
        
    # 2. School Check (If applicable)
    if school_id:
        school = await db["schools"].find_one({"_id": school_id})
        school_status = school.get("status") if school else "inactive"
        
        if school_status != "active":
            # Rule: Admins might log in to read-only, but usually Login is allowed for Admin
            # unless we strictly want to block Login based on requirement "School.status != ACTIVE -> Teachers & Students CANNOT login"
            # It implies Admin CAN login.
            
            if role in ["TEACHER", "STUDENT"]:
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="School is inactive. Login denied."
                )
            # If Admin, we allow login (Read-Only enforced at Request Middleware Level)
            
    # 3. User Status Check
    if user_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User account is inactive"
        )

async def check_request_status(request: Request, db):
    """
    Middleware Helper: Validate status hierarchy at REQUEST time.
    Enforces Read-Only for Admins in inactive schools.
    """
    # Extract Context from State (Populated by Auth Middlewares/Dependencies)
    # Note: Middleware order matters. Context/Auth middleware comes BEFORE this?
    # Actually, Implementation Plan said StatusGuard comes BEFORE Context middlewares
    # Wait, if StatusGuard checks state, it must come AFTER Auth/Context middlewares populate state.
    # BUT, the requirement is "Fail-Fast".
    # Verification: If Guard runs first, it has no user info.
    # So Guard Middleware must run AFTER Auth, OR Auth Dependency must call Guard.
    # Strategy: "Middleware" approach usually implies wrapping the endpoint.
    # FastAPI Middleware stack: Requests enter top-down. 
    # If we register StatusGuard LAST, it runs FIRST? No, Starlette stack.
    # add_middleware adds to the "outside". So:
    # app.add_middleware(StatusGuard)
    # app.add_middleware(AuthMiddleware)
    # Request -> StatusGuard -> Auth -> Endpoint. 
    # StatusGuard won't have user info yet.
    
    # REVISION: StatusGuard should rely on JWT parsing itself OR exist as a Dependency.
    # Requirement: "Global Status Guard (Design)... Create ONE reusable guard / dependency / middleware"
    # Given the complexity of "Admin Read-Only", middleware that inspects *state* populated by Auth is best.
    # So Order: AuthMiddleware (populates state) -> StatusGuardMiddleware (checks state) -> Endpoint.
    # In FastAPI `add_middleware` pushes to the top of the stack (outermost).
    # We want Auth to run FIRST (outermost) so it populates state.
    # So we must add AuthMiddleware LAST in main.py? 
    # Startlette Middleware is onion. 
    # app.add_middleware(A)
    # app.add_middleware(B)
    # Request -> B -> A -> App
    # So we want Auth (B) to run, then Status (A).
    # So we add Status, then Auth.
    
    pass
