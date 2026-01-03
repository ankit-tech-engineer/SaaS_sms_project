from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.security_school import decode_access_token

class SchoolUserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Initialize State
        request.state.school_user = None
        request.state.school_id = None
        
        # 2. Check for Token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            
            if payload and payload.get("type") == "SCHOOL_USER":
                # 3. Inject Context
                request.state.school_user = {
                    "id": payload.get("sub"),
                    "role": payload.get("role"),
                    "school_id": payload.get("school_id")
                }
                request.state.school_id = payload.get("school_id")
        
        # 4. Enforce Context on /school routes (Optional here, typically handled by Dependencies)
        # But per requirements, we should ensure context is locked.
        # This middleware acts more as a helper to populate state. 
        # The strict Auth check happens in 'get_current_school_user' dependency.
        
        response = await call_next(request)
        return response
