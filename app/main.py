from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from app.utils.response import APIResponse

from app.core.config import settings
from app.core.database import db
from app.middlewares.audit import AuditMiddleware
from app.middlewares.auth import AuthMiddleware
from app.middlewares.org_context import OrgContextMiddleware
from app.modules.auth.service import AuthService

# Routers
from app.modules.auth.router import router as auth_router
from app.modules.platform_admin.router import router as platform_admin_router
from app.modules.plans.router import router as plans_router
from app.modules.organizations.router import router as org_router
from app.modules.subscriptions.router import router as sub_router
from app.modules.payments.router import router as payment_router
from app.modules.org_auth.router import router as org_auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db.connect()
    # Init Super Admin
    await AuthService.init_super_admin()
    
    yield
    
    # Shutdown
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return APIResponse.error(
        message=exc.detail,
        status_code=exc.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Get the first error message for simplicity
    errors = exc.errors()
    error_msg = f"Validation Error: {errors[0]['msg']} in {errors[0]['loc']}" if errors else "Validation Error"
    return APIResponse.error(
        message=error_msg,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        data=jsonable_encoder(errors)
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # In production, log the error here
    return APIResponse.error(
        message="Internal Server Error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        data=str(exc) if settings.PROJECT_NAME else None # Show error in dev
    )

# Middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS] or ["*"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware) # Platform Auth
app.add_middleware(OrgContextMiddleware) # Org Context Auth

# --- Platform Routes Group ---
platform_router = APIRouter()

platform_router.include_router(auth_router, prefix="/auth", tags=["Platform: Auth"])
platform_router.include_router(platform_admin_router, prefix="/admin", tags=["Platform: Admin"])
platform_router.include_router(plans_router, prefix="/plans", tags=["Platform: Plans"])
platform_router.include_router(sub_router, prefix="/subscriptions", tags=["Platform: Subscriptions"])
platform_router.include_router(payment_router, prefix="/payments", tags=["Platform: Payments"])

# Mount Platform Routes
app.include_router(platform_router, prefix="/platform")

# --- Public Routes Group ---
public_router = APIRouter()
public_router.include_router(org_router, prefix="/org", tags=["Public: Organizations"])

# Mount Public Routes
app.include_router(public_router, prefix="/public")

# --- Org Routes Group ---
org_app_router = APIRouter()
org_app_router.include_router(org_auth_router, prefix="/auth", tags=["Org: Auth"])

# Mount Org Routes
app.include_router(org_app_router, prefix="/org")


@app.get("/")
async def root():
    return {"message": "SaaS Platform API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
