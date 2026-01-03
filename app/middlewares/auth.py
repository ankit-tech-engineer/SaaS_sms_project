from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from jose import jwt, JWTError

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/platform"):
            # Exclude login endpoint
            if request.url.path.startswith("/platform/auth/login") or request.url.path.startswith("/platform/auth/token") or request.url.path.startswith("/platform/payments/webhook"):
                 return await call_next(request)
            
            # Allow OpenAPI docs
            if request.url.path.startswith(f"{settings.API_V1_STR}/openapi.json") or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
                 return await call_next(request)

            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                 return JSONResponse(
                     status_code=status.HTTP_401_UNAUTHORIZED,
                     content={"detail": "Missing or invalid authentication token"}
                 )
            
            token = auth_header.split(" ")[1]
            try:
                jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            except JWTError:
                 return JSONResponse(
                     status_code=status.HTTP_401_UNAUTHORIZED,
                     content={"detail": "Invalid token"}
                 )

        response = await call_next(request)
        return response
