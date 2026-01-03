from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request, status
from jose import jwt, JWTError
from app.core.config import settings

class OrgContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only apply to /org routes, but exclude login endpoints
        if request.url.path.startswith("/org") and not request.url.path.startswith("/org/auth/login") and not request.url.path.startswith("/org/auth/token"):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"success": False, "message": "Missing authentication token", "error": True}
                )
            
            token = auth_header.split(" ")[1]
            try:
                # Validate Token using ORG_SECRET_KEY
                payload = jwt.decode(token, settings.ORG_SECRET_KEY, algorithms=[settings.ALGORITHM])
                org_id = payload.get("org_id")
                user_id = payload.get("sub")
                
                if not org_id:
                     return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"success": False, "message": "Invalid token context", "error": True}
                    )
                
                # Inject into state
                request.state.org_id = org_id
                request.state.user_id = user_id
                
            except JWTError:
                 return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"success": False, "message": "Invalid authentication token", "error": True}
                )
        
        response = await call_next(request)
        return response
